import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.auth import require_user
from api.deals import Deal, find_deals, pick_deals
from api.deps import get_session, get_write_session
from api.main import app
from api.send_alerts import send_alerts
from db.models import (
    Base,
    CanonicalProduct,
    Listing,
    PriceAlert,
    PriceHistory,
    Retailer,
    SavedProduct,
    User,
)
from db.session import get_engine

PREFIX = "/api/v1"
HEADERS = {"X-Quote-Yard": "1"}
NOW = datetime.now(timezone.utc)


class FakeMailer:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def send(self, to, subject, body):
        if self.fail:
            raise OSError("smtp down")
        self.sent.append((to, subject, body))


@pytest.fixture(scope="module")
def engine():
    eng = get_engine()
    try:
        with eng.connect():
            pass
    except OperationalError:
        pytest.skip("PostgreSQL not reachable")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def s(engine):
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    trans.rollback()
    conn.close()


@pytest.fixture
def user(s):
    u = User(email="anu@example.com", password_hash="x", email_verified_at=NOW)
    s.add(u)
    s.flush()
    return u


@pytest.fixture
def client(s, user):
    app.dependency_overrides[get_session] = lambda: s
    app.dependency_overrides[get_write_session] = lambda: s
    app.dependency_overrides[require_user] = lambda: user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def shops(s):
    rows = [Retailer(name=n) for n in ("ShopA", "ShopB")]
    s.add_all(rows)
    s.flush()
    return rows


def product(s, key="zed", ram=8, storage=128, model="zed 9", name=None):
    p = CanonicalProduct(brand="Testco", name=name or f"Testco Zed {ram}/{storage}",
                         product_type="Mobile Phone", model=model, network="5G", ram_gb=ram,
                         storage_gb=storage, match_key=f"t|{key}", matching_version="1.2")
    s.add(p)
    s.flush()
    return p


counter = [0]


def listing(s, shop, price, history=(), p=None, availability="In stock", brand="Testco", name=None):
    """history: (price, days_ago) points, oldest first; the current price is added today."""
    counter[0] += 1
    l = Listing(retailer_id=shop.id, url=f"https://{shop.name}/{counter[0]}",
                name=name or f"Listing {counter[0]}", brand=brand, brand_status="matched",
                current_price=price, availability=availability, taxonomy_version="1",
                brands_version="1", canonical_product_id=p.id if p else None)
    s.add(l)
    s.flush()
    for value, days in list(history) + [(price, 0)]:
        s.add(PriceHistory(listing_id=l.id, price=value, availability="In stock",
                           recorded_at=NOW - timedelta(days=days)))
    s.flush()
    return l


# ---- deal rule -------------------------------------------------------------------

def test_real_drop_of_500_is_a_deal(s, shops):
    listing(s, shops[0], 19500, [(20000, 1)])
    (d,) = find_deals(s)
    assert (d.kind, d.price, d.compared_price, d.saving) == ("price_drop", 19500, 20000, 500)
    assert d.label == "Lowest since we began tracking"


def test_drop_under_500_is_not(s, shops):
    listing(s, shops[0], 19501, [(20000, 1)])
    assert find_deals(s) == []


def test_price_that_never_moved_is_not(s, shops):
    listing(s, shops[0], 100, [(100, 5)])
    assert find_deals(s) == []


def test_price_rise_is_not(s, shops):
    listing(s, shops[0], 21000, [(20000, 1)])
    assert find_deals(s) == []


def test_not_at_its_lowest_is_not(s, shops):
    listing(s, shops[0], 20000, [(18000, 20), (21000, 1)])
    assert find_deals(s) == []


def test_old_low_outside_90_days_does_not_count(s, shops):
    listing(s, shops[0], 20000, [(18000, 120), (21000, 1)])
    assert [d.price for d in find_deals(s)] == [20000]


def test_drop_older_than_a_week_is_not(s, shops):
    l = listing(s, shops[0], 19000, [(20000, 30), (19000, 10)])
    # the "today" point has the same price, so the change was 10 days ago
    assert l and find_deals(s) == []


def test_ninety_days_label_needs_ninety_days_of_history(s, shops):
    listing(s, shops[0], 19000, [(20000, 95), (20000, 1)])
    assert find_deals(s)[0].label == "Lowest in 90 days"


def test_out_of_stock_is_not(s, shops):
    listing(s, shops[0], 19000, [(20000, 1)], availability="Out of stock")
    assert find_deals(s) == []


def test_stale_listing_is_not(s, shops):
    old = listing(s, shops[0], 19000, [(20000, 1)])
    old.last_seen_at = NOW - timedelta(days=5)
    s.flush()
    assert find_deals(s) == []


def test_drop_ignored_when_another_store_is_cheaper(s, shops):
    p = product(s)
    listing(s, shops[0], 19000, [(20000, 1)], p=p)
    listing(s, shops[1], 18800, p=p)
    assert [d.kind for d in find_deals(s)] == []  # gap of 200 is under the minimum too


def test_colours_of_one_product_give_one_deal(s, shops):
    p = product(s)
    listing(s, shops[0], 19000, [(20000, 1)], p=p)
    listing(s, shops[0], 19000, [(19800, 1)], p=p)
    (d,) = find_deals(s)
    assert d.saving == 1000 and d.name == p.name


def test_store_gap(s, shops):
    p = product(s)
    listing(s, shops[0], 19000, p=p)
    listing(s, shops[1], 19500, p=p)
    (d,) = find_deals(s)
    assert (d.kind, d.retailer, d.compared_retailer, d.saving) == ("store_gap", "ShopA", "ShopB", 500)


def test_store_gap_under_500_is_not(s, shops):
    p = product(s)
    listing(s, shops[0], 19000, p=p)
    listing(s, shops[1], 19499, p=p)
    assert find_deals(s) == []


# ---- picking ---------------------------------------------------------------------

def deal(i, kind="price_drop", brand=None):
    return Deal(kind, f"k{i:02}", f"N{i}", brand or f"B{i}", "S", 1, 2, None, 1, "L", NOW)


def test_same_picks_all_day_and_changes_between_days():
    deals = [deal(i) for i in range(30)]
    day = date(2026, 11, 1)
    assert pick_deals(deals, day) == pick_deals(list(reversed(deals)), day)
    assert len(pick_deals(deals, day)) == 5
    assert pick_deals(deals, day) != pick_deals(deals, date(2026, 11, 2))


def test_prefers_different_brands():
    deals = [deal(i, brand="Same") for i in range(10)] + [deal(20), deal(21)]
    brands = [d.brand for d in pick_deals(deals, date(2026, 11, 1))]
    assert {"B20", "B21", "Same"} <= set(brands) and len(brands) == 5


def test_at_most_two_store_gaps():
    deals = [deal(i, "store_gap") for i in range(6)] + [deal(i + 10) for i in range(6)]
    kinds = [d.kind for d in pick_deals(deals, date(2026, 11, 1))]
    assert kinds.count("store_gap") == 2 and len(kinds) == 5


def test_never_padded():
    assert len(pick_deals([deal(1), deal(2)], date(2026, 11, 1))) == 2


def test_public_deals_open_without_login_and_without_links(s, shops):
    listing(s, shops[0], 19000, [(20000, 1)])
    app.dependency_overrides[get_session] = lambda: s
    try:
        r = TestClient(app).get(f"{PREFIX}/public/deals")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200 and r.json()[0]["saving"] == 1000
    assert "url" not in r.json()[0] and "https://" not in r.text


# ---- saved items -----------------------------------------------------------------

def test_save_is_idempotent_and_remembers_the_price(client, s, shops):
    p = product(s)
    listing(s, shops[0], 19000, p=p)
    for _ in range(2):
        r = client.put(f"{PREFIX}/me/saved/{p.id}", headers=HEADERS)
        assert r.status_code == 200 and r.json()["price_when_saved"] == 19000
    items = client.get(f"{PREFIX}/me/saved").json()
    assert [i["product"]["id"] for i in items] == [p.id]
    assert client.delete(f"{PREFIX}/me/saved/{p.id}", headers=HEADERS).status_code == 204
    assert client.get(f"{PREFIX}/me/saved").json() == []


def test_saved_items_belong_to_their_user(client, s, shops):
    p = product(s)
    other = User(email="other@example.com", password_hash="x", email_verified_at=NOW)
    s.add(other)
    s.flush()
    client.put(f"{PREFIX}/me/saved/{p.id}", headers=HEADERS)
    app.dependency_overrides[require_user] = lambda: other
    assert client.get(f"{PREFIX}/me/saved").json() == []
    client.delete(f"{PREFIX}/me/saved/{p.id}", headers=HEADERS)  # cannot remove someone else's
    assert s.scalar(select(func.count()).select_from(SavedProduct)) == 1


def test_me_routes_need_login_and_header(s):
    app.dependency_overrides[get_session] = lambda: s
    try:
        c = TestClient(app)
        assert c.get(f"{PREFIX}/me/saved").status_code == 401
        assert c.get(f"{PREFIX}/me/alerts").status_code == 401
        assert c.put(f"{PREFIX}/me/saved/1").status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_unknown_product_404(client):
    assert client.put(f"{PREFIX}/me/saved/999999", headers=HEADERS).status_code == 404
    r = client.put(f"{PREFIX}/me/alerts/999999", json={"target_price": 5}, headers=HEADERS)
    assert r.status_code == 404


# ---- alerts ----------------------------------------------------------------------

@pytest.mark.parametrize("target", [0, -5])
def test_bad_target_rejected(client, s, target):
    p = product(s)
    r = client.put(f"{PREFIX}/me/alerts/{p.id}", json={"target_price": target}, headers=HEADERS)
    assert r.status_code == 422


def test_alert_api_set_change_delete(client, s):
    p = product(s)
    url = f"{PREFIX}/me/alerts/{p.id}"
    assert client.put(url, json={"target_price": 100}, headers=HEADERS).json()["target_price"] == 100
    assert client.put(url, json={"target_price": 90}, headers=HEADERS).json()["target_price"] == 90
    assert len(client.get(f"{PREFIX}/me/alerts").json()) == 1
    assert client.delete(url, headers=HEADERS).status_code == 204
    assert client.get(f"{PREFIX}/me/alerts").json() == []


def alert(s, user, p, target):
    a = PriceAlert(user_id=user.id, canonical_product_id=p.id, target_price=target)
    s.add(a)
    s.flush()
    return a


def test_alert_fires_once_and_again_only_for_a_lower_price(s, user, shops):
    p = product(s)
    l = listing(s, shops[0], 19000, p=p)
    alert(s, user, p, 20000)
    mailer = FakeMailer()
    assert send_alerts(s, mailer)["sent"] == 1
    assert mailer.sent[0][0] == user.email and "19,000" in mailer.sent[0][2]
    assert l.url in mailer.sent[0][2]
    assert send_alerts(s, mailer)["sent"] == 0
    l.current_price = 18000
    s.flush()
    assert send_alerts(s, mailer)["sent"] == 1


def test_alert_not_below_target_stays_quiet_and_rearms(s, user, shops):
    p = product(s)
    l = listing(s, shops[0], 20000, p=p)
    a = alert(s, user, p, 20000)
    mailer = FakeMailer()
    assert send_alerts(s, mailer)["sent"] == 0  # at the target is not below it
    l.current_price = 19000
    s.flush()
    send_alerts(s, mailer)
    l.current_price = 21000
    s.flush()
    send_alerts(s, mailer)
    assert a.last_notified_price is None
    l.current_price = 19000
    s.flush()
    assert send_alerts(s, mailer)["sent"] == 1


def test_alert_ignores_stale_and_out_of_stock(s, user, shops):
    p = product(s)
    alert(s, user, p, 20000)
    listing(s, shops[0], 100, p=p, availability="Out of stock")
    stale = listing(s, shops[1], 100, p=p)
    stale.last_seen_at = NOW - timedelta(days=5)
    s.flush()
    assert send_alerts(s, FakeMailer())["sent"] == 0


def test_unverified_user_gets_no_alert(s, user, shops):
    p = product(s)
    listing(s, shops[0], 100, p=p)
    alert(s, user, p, 20000)
    user.email_verified_at = None
    s.flush()
    assert send_alerts(s, FakeMailer()) == {"checked": 0, "sent": 0, "failed": 0}


def test_failed_email_is_retried_next_run(s, user, shops):
    p = product(s)
    listing(s, shops[0], 100, p=p)
    a = alert(s, user, p, 20000)
    assert send_alerts(s, FakeMailer(fail=True))["failed"] == 1
    assert a.last_notified_price is None
    assert send_alerts(s, FakeMailer())["sent"] == 1


def test_dry_run_sends_and_saves_nothing(s, user, shops):
    p = product(s)
    listing(s, shops[0], 100, p=p)
    a = alert(s, user, p, 20000)
    mailer = FakeMailer()
    assert send_alerts(s, mailer, dry_run=True)["sent"] == 1
    assert not mailer.sent and a.last_notified_price is None


# ---- variants and newest ----------------------------------------------------------

def test_variants_list_same_model_only(client, s, shops):
    a = product(s, "a", 8, 128)
    b = product(s, "b", 8, 256)
    c = product(s, "c", 8, 128, model="zed 9 pro")
    for p in (a, b, c):
        listing(s, shops[0], 100, p=p)
    ids = [v["id"] for v in client.get(f"{PREFIX}/products/{a.id}/variants").json()]
    assert ids == [a.id, b.id]
    assert client.get(f"{PREFIX}/products/999999/variants").status_code == 404


def test_sort_newest(client, s, shops):
    a = product(s, "a", name="Testco Old")
    b = product(s, "b", name="Testco New")
    listing(s, shops[0], 100, p=a)
    listing(s, shops[0], 100, p=b)
    a.created_at = NOW - timedelta(days=5)
    s.flush()
    names = [i["name"] for i in client.get(f"{PREFIX}/products?sort=newest").json()["items"]]
    assert names == ["Testco New", "Testco Old"]

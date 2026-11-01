from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.deps import get_session, get_write_session
from api.mailer import get_mailer
from api.main import app
from api.routes.vendor import VENDOR_COOKIE, today_in_india
from api.security import hash_secret
from db.models import (Base, CanonicalProduct, Listing, Retailer, User, Vendor, VendorAuditLog,
                       VendorOffer)
from db.session import get_engine

P = "/api/v1"
H = {"X-Quote-Yard": "1"}
ADMIN = "boss@example.com"
SHOP = "shop@example.com"
PW = "correct horse"


class FakeMailer:
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append((to, subject, body))

    def token(self):
        return re.search(r"#(\S+)", self.sent[-1][2]).group(1)


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
def ctx(engine, monkeypatch):
    monkeypatch.setenv("QUOTE_YARD_ADMIN_EMAILS", ADMIN)
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    mailer = FakeMailer()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_write_session] = lambda: session
    app.dependency_overrides[get_mailer] = lambda: mailer
    yield session, mailer
    app.dependency_overrides.clear()
    session.close()
    trans.rollback()
    conn.close()


def customer(session, email):
    session.add(User(email=email, first_name="A", password_hash=hash_secret(PW),
                     email_verified_at=datetime.now(timezone.utc)))
    session.flush()
    client = TestClient(app)
    assert client.post(f"{P}/auth/login", json={"email": email, "password": PW}, headers=H).status_code == 200
    return client


def product(session, price=10000):
    shop = Retailer(name="Teststore")
    session.add(shop)
    session.flush()
    p = CanonicalProduct(match_key="testco|zed", name="Testco Zed", brand="Testco", model="zed",
                         category="Mobiles & Tablets", product_type="Mobile Phone",
                         network="5G", ram_gb=8, storage_gb=128, matching_version="1.3")
    session.add(p)
    session.flush()
    session.add(Listing(retailer_id=shop.id, url="https://t.example/1", name="Zed", brand="Testco",
                        brand_status="matched", current_price=price, availability="In stock",
                        taxonomy_version="1.0", brands_version="1.1", canonical_product_id=p.id))
    session.flush()
    return p


JOIN = dict(password=PW, shop_name="Anu Mobiles", owner_name="Anu", phone="+91 98470 12345",
            address="MG Road", town="Kochi", district="Ernakulam")


def joined(session, mailer, status="approved"):
    admin = customer(session, ADMIN)
    assert admin.post(f"{P}/admin/invites", json={"email": SHOP}, headers=H).status_code == 201
    client = TestClient(app)
    reply = client.post(f"{P}/vendor/join", json={**JOIN, "token": mailer.token()}, headers=H)
    assert reply.status_code == 201
    assert reply.json()["status"] == "pending" and reply.json()["phone"] == "9847012345"
    if status == "approved":
        vendor = session.scalar(select(Vendor))
        assert admin.post(f"{P}/admin/vendors/{vendor.id}/decision", json={"decision": "approve"},
                          headers=H).status_code == 200
    return admin, client


def dates(start=0, days=6):
    today = today_in_india()
    return {"starts_on": str(today + timedelta(days=start)), "ends_on": str(today + timedelta(days=start + days))}


def test_admin_routes_are_closed_to_everyone_else(ctx):
    session, _ = ctx
    assert TestClient(app).get(f"{P}/admin/vendors").status_code == 401
    assert customer(session, "someone@example.com").get(f"{P}/admin/vendors").status_code == 403
    me = customer(session, ADMIN).get(f"{P}/auth/me").json()
    assert me["is_admin"] is True


def test_invite_is_one_time_and_needed_to_join(ctx):
    session, mailer = ctx
    admin = customer(session, ADMIN)
    bad = TestClient(app).post(f"{P}/vendor/join", json={**JOIN, "token": "nope"}, headers=H)
    assert bad.status_code == 400
    admin.post(f"{P}/admin/invites", json={"email": SHOP}, headers=H)
    token = mailer.token()
    assert mailer.sent[-1][0] == SHOP
    assert TestClient(app).post(f"{P}/vendor/join", json={**JOIN, "token": token}, headers=H).status_code == 201
    assert TestClient(app).post(f"{P}/vendor/join", json={**JOIN, "token": token}, headers=H).status_code == 400
    assert admin.post(f"{P}/admin/invites", json={"email": SHOP}, headers=H).status_code == 409
    assert admin.get(f"{P}/admin/invites").json()[0]["state"] == "joined"


def test_new_invite_cancels_the_old_link(ctx):
    session, mailer = ctx
    admin = customer(session, ADMIN)
    admin.post(f"{P}/admin/invites", json={"email": SHOP}, headers=H)
    old = mailer.token()
    admin.post(f"{P}/admin/invites", json={"email": SHOP}, headers=H)
    assert TestClient(app).post(f"{P}/vendor/join", json={**JOIN, "token": old}, headers=H).status_code == 400


@pytest.mark.parametrize("field,value", [("phone", "12345"), ("district", "Chennai"),
                                         ("gst_number", "NOTGST"), ("shop_name", " ")])
def test_join_details_are_checked(ctx, field, value):
    session, mailer = ctx
    customer(session, ADMIN).post(f"{P}/admin/invites", json={"email": SHOP}, headers=H)
    reply = TestClient(app).post(f"{P}/vendor/join", json={**JOIN, "token": mailer.token(), field: value}, headers=H)
    assert reply.status_code == 422


def test_only_an_approved_shop_can_publish(ctx):
    session, mailer = ctx
    p = product(session)
    admin, shop = joined(session, mailer, status="pending")
    body = {"product_id": p.id, "price": 9000, **dates()}
    assert shop.post(f"{P}/vendor/offers", json=body, headers=H).status_code == 403
    vendor = session.scalar(select(Vendor))
    admin.post(f"{P}/admin/vendors/{vendor.id}/decision", json={"decision": "approve"}, headers=H)
    assert shop.post(f"{P}/vendor/offers", json=body, headers=H).status_code == 201


def test_offer_is_shown_labelled_and_stays_out_of_store_prices(ctx):
    session, mailer = ctx
    p = product(session)
    admin, shop = joined(session, mailer)
    assert shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 9000, **dates()}, headers=H).status_code == 201
    offers = admin.get(f"{P}/products/{p.id}/local-offers").json()
    assert len(offers) == 1
    assert offers[0]["source"] == "verified_vendor" and offers[0]["price"] == 9000
    assert offers[0]["map_url"].startswith("https://www.google.com/maps/search/")
    assert "gst_number" not in offers[0] and "email" not in offers[0]
    detail = admin.get(f"{P}/products/{p.id}").json()
    assert detail["min_price"] == 10000 and detail["offers"][0]["source"] == "scraped_listing"
    compare = admin.get(f"{P}/compare/{p.id}").json()
    assert compare["retailers"][0]["best"]["price"] == 10000 and compare["retailers"][0]["cheapest_listed"]


@pytest.mark.parametrize("price,when,why", [
    (4999, dates(), "too far"), (15001, dates(), "too far"),
    (9000, dates(start=-1), "start date"), (9000, dates(days=31), "at most 31"),
    (9000, dates(start=31), "at most 30"),
])
def test_automatic_checks_refuse_bad_offers(ctx, price, when, why):
    session, mailer = ctx
    p = product(session)
    _, shop = joined(session, mailer)
    reply = shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": price, **when}, headers=H)
    assert reply.status_code == 422 and why in reply.json()["detail"]


def test_price_limits_themselves_are_allowed(ctx):
    session, mailer = ctx
    p = product(session)
    _, shop = joined(session, mailer)
    assert shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 5000, **dates()}, headers=H).status_code == 201
    offer_id = shop.get(f"{P}/vendor/offers").json()[0]["id"]
    assert shop.put(f"{P}/vendor/offers/{offer_id}", json={"price": 15000, **dates()}, headers=H).status_code == 200


def test_scheduled_and_expired_offers_are_hidden(ctx):
    session, mailer = ctx
    p = product(session)
    admin, shop = joined(session, mailer)
    shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 9000, **dates(start=2)}, headers=H)
    assert admin.get(f"{P}/products/{p.id}/local-offers").json() == []
    assert shop.get(f"{P}/vendor/offers").json()[0]["state"] == "scheduled"
    offer = session.scalar(select(VendorOffer))
    offer.starts_on = today_in_india() - timedelta(days=5)
    offer.ends_on = today_in_india() - timedelta(days=1)
    session.flush()
    assert admin.get(f"{P}/products/{p.id}/local-offers").json() == []
    assert shop.get(f"{P}/vendor/offers").json()[0]["state"] == "expired"


def test_one_running_offer_per_product_but_expired_can_be_replaced(ctx):
    session, mailer = ctx
    p = product(session)
    _, shop = joined(session, mailer)
    body = {"product_id": p.id, "price": 9000, **dates()}
    assert shop.post(f"{P}/vendor/offers", json=body, headers=H).status_code == 201
    assert shop.post(f"{P}/vendor/offers", json=body, headers=H).status_code == 409
    old = session.scalar(select(VendorOffer))
    old.starts_on = today_in_india() - timedelta(days=5)
    old.ends_on = today_in_india() - timedelta(days=1)
    session.flush()
    assert shop.post(f"{P}/vendor/offers", json=body, headers=H).status_code == 201
    assert old.closed_by == "replaced"


def test_a_shop_cannot_touch_another_shops_offer(ctx):
    session, mailer = ctx
    p = product(session)
    _, shop = joined(session, mailer)
    shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 9000, **dates()}, headers=H)
    offer = session.scalar(select(VendorOffer))
    other = Vendor(email="other@example.com", password_hash=hash_secret(PW), shop_name="Other",
                   owner_name="O", phone="9847000000", address="A", town="T", district="Thrissur",
                   status="approved")
    session.add(other)
    session.flush()
    rival = TestClient(app)
    assert rival.post(f"{P}/vendor/login", json={"email": other.email, "password": PW}, headers=H).status_code == 200
    assert rival.put(f"{P}/vendor/offers/{offer.id}", json={"price": 5000, **dates()}, headers=H).status_code == 404
    assert rival.delete(f"{P}/vendor/offers/{offer.id}", headers=H).status_code == 404
    assert offer.price == 9000 and offer.closed_at is None


def test_suspending_hides_offers_and_reinstating_restores_them(ctx):
    session, mailer = ctx
    p = product(session)
    admin, shop = joined(session, mailer)
    shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 9000, **dates()}, headers=H)
    vendor = session.scalar(select(Vendor))
    url = f"{P}/admin/vendors/{vendor.id}/decision"
    assert admin.post(url, json={"decision": "suspend"}, headers=H).status_code == 200
    assert admin.get(f"{P}/products/{p.id}/local-offers").json() == []
    assert shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 9000, **dates()}, headers=H).status_code == 403
    assert admin.post(url, json={"decision": "reject"}, headers=H).status_code == 409
    assert admin.post(url, json={"decision": "reinstate"}, headers=H).status_code == 200
    assert len(admin.get(f"{P}/products/{p.id}/local-offers").json()) == 1


def test_admin_removal_is_final_and_everything_is_audited(ctx):
    session, mailer = ctx
    p = product(session)
    admin, shop = joined(session, mailer)
    shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 9000, **dates()}, headers=H)
    offer = admin.get(f"{P}/admin/offers").json()[0]
    assert admin.delete(f"{P}/admin/offers/{offer['id']}", headers=H).status_code == 204
    assert admin.get(f"{P}/products/{p.id}/local-offers").json() == []
    assert shop.put(f"{P}/vendor/offers/{offer['id']}", json={"price": 9000, **dates()}, headers=H).status_code == 404
    actions = {r.action for r in session.scalars(select(VendorAuditLog))}
    assert {"invited", "joined", "approve", "offer_created", "offer_removed"} <= actions
    assert admin.get(f"{P}/admin/audit").json()[0]["action"] == "offer_removed"


def test_password_reset_logs_out_and_reply_hides_unknown_shops(ctx):
    session, mailer = ctx
    _, shop = joined(session, mailer)
    count = len(mailer.sent)
    first = shop.post(f"{P}/vendor/forgot-password", json={"email": "nobody@example.com"}, headers=H)
    assert first.status_code == 202 and len(mailer.sent) == count
    second = shop.post(f"{P}/vendor/forgot-password", json={"email": SHOP}, headers=H)
    assert second.json() == first.json()
    token = mailer.token()
    assert shop.post(f"{P}/vendor/reset-password", json={"token": token, "new_password": "new password 1"}, headers=H).status_code == 200
    assert shop.get(f"{P}/vendor/me").status_code == 401
    assert shop.post(f"{P}/vendor/reset-password", json={"token": token, "new_password": "new password 2"}, headers=H).status_code == 400
    assert shop.post(f"{P}/vendor/login", json={"email": SHOP, "password": "new password 1"}, headers=H).status_code == 200


def test_shop_login_is_not_a_customer_login(ctx):
    session, mailer = ctx
    p = product(session)
    _, shop = joined(session, mailer)
    assert VENDOR_COOKIE in shop.cookies
    assert shop.get(f"{P}/products/{p.id}").status_code == 401
    assert shop.get(f"{P}/admin/vendors").status_code == 401


def test_changes_need_the_app_header(ctx):
    session, mailer = ctx
    p = product(session)
    _, shop = joined(session, mailer)
    assert shop.post(f"{P}/vendor/offers", json={"product_id": p.id, "price": 9000, **dates()}).status_code == 403

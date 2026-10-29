import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.deps import get_session
from api.main import app
from db.models import Base, CanonicalProduct, Listing, ListingCategory, PriceHistory, Retailer
from db.session import get_engine

PREFIX = "/api/v1"


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
def ctx(engine):
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app), session
    app.dependency_overrides.clear()
    session.close()
    trans.rollback()
    conn.close()


@pytest.fixture
def shops(ctx):
    _, session = ctx
    rs = [Retailer(name=n) for n in ("ShopA", "ShopB", "ShopC")]
    session.add_all(rs)
    session.flush()
    return rs


def product(session, key="zed9", name="Testco Zed 9 5G [8 GB RAM, 128 GB]", brand="Testco",
            model="zed 9", **over):
    fields = dict(brand=brand, name=name, category="Mobiles & Tablets",
                  product_type="Mobile Phone", model=model, network="5G", ram_gb=8,
                  storage_gb=128, match_key=f"testco|{key}", matching_version="1.1")
    fields.update(over)
    p = CanonicalProduct(**fields)
    session.add(p)
    session.flush()
    return p


def offer(session, p, shop, price, availability="In stock", box_note=None, days_ago=None, n=[0]):
    n[0] += 1
    listing = Listing(
        retailer_id=shop.id, url=f"https://{shop.name}/{n[0]}", name=f"{p.name} #{n[0]}",
        brand=p.brand, brand_status="matched", current_price=price,
        availability=availability, taxonomy_version="1.0", brands_version="1.1",
        canonical_product_id=p.id, box_note=box_note,
    )
    if days_ago is not None:
        listing.last_seen_at = listing.first_seen_at = (
            datetime.now(timezone.utc) - timedelta(days=days_ago))
    listing.categories.append(ListingCategory(
        category="Mobiles & Tablets", product_type="Mobile Phone",
        mapping_status="mapped", raw_category="Mobiles"))
    listing.price_history.append(PriceHistory(price=price, availability=availability))
    session.add(listing)
    session.flush()
    return listing


def get(client, path, **params):
    return client.get(PREFIX + path, params=params)


# ---- /products ---------------------------------------------------------------

def test_list_products_with_stats(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 20000)
    offer(s, p, a, 21000)
    offer(s, p, b, 19500)
    body = get(client, "/products").json()
    assert body["total"] == 1
    item = body["items"][0]
    assert (item["listings"], item["retailers"], item["min_price"], item["max_price"]) == (
        3, 2, 19500, 21000)
    assert item["specs"] == {"model": "zed 9", "network": "5G", "ram_gb": 8,
                             "storage_gb": 128, "package": None, "ta_code": None}


def test_orphan_products_hidden_from_list(ctx, shops):
    client, s = ctx
    product(s, key="orphan", name="Testco Orphan [8 GB RAM, 128 GB]")
    assert get(client, "/products").json()["total"] == 0


def test_min_retailers_filter(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    two = product(s, key="two", name="Testco Two")
    one = product(s, key="one", name="Testco One")
    offer(s, two, a, 100), offer(s, two, b, 110), offer(s, one, a, 100)
    names = [i["name"] for i in get(client, "/products", min_retailers=2).json()["items"]]
    assert names == ["Testco Two"]


def test_search_matches_name_brand_or_model(ctx, shops):
    client, s = ctx
    a = shops[0]
    # name lacks "galaxy"-style words, but the model carries them
    p = product(s, key="q", name="Testco A17 5G [6 GB RAM, 128 GB]", model="a17 ultra")
    offer(s, p, a, 100)
    assert get(client, "/products", q="testco ultra").json()["total"] == 1
    assert get(client, "/products", q="testco missing").json()["total"] == 0
    assert get(client, "/products", q="100%_").json()["total"] == 0  # wildcards escaped


def test_filters_and_sorts(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    cheap = product(s, key="c", name="Testco Cheap")
    dear = product(s, key="d", name="Testco Dear", brand="Otherco")
    offer(s, cheap, a, 100), offer(s, dear, a, 900), offer(s, dear, b, 950)
    ids = lambda **kw: [i["name"] for i in get(client, "/products", **kw).json()["items"]]
    assert ids(sort="price_desc") == ["Testco Dear", "Testco Cheap"]
    assert ids(sort="retailers") == ["Testco Dear", "Testco Cheap"]
    assert ids(brand="otherco") == ["Testco Dear"]
    assert ids(max_price=500) == ["Testco Cheap"]
    assert ids(min_price=500) == ["Testco Dear"]
    assert ids(product_type="mobile phone", sort="name") == ["Testco Cheap", "Testco Dear"]


def test_out_of_stock_does_not_set_price(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 50, availability="Out of stock")
    offer(s, p, b, 300)
    item = get(client, "/products").json()["items"][0]
    assert (item["min_price"], item["max_price"]) == (300, 300)


@pytest.mark.parametrize("params", [
    {"limit": 0}, {"limit": 101}, {"min_retailers": 0}, {"sort": "random"},
    {"min_price": 10, "max_price": 5}, {"q": "x" * 101},
])
def test_bad_parameters_rejected(ctx, shops, params):
    client, _ = ctx
    assert get(client, "/products", **params).status_code == 422


# ---- /products/{id} and prices ------------------------------------------------

def test_product_detail_lists_offers_cheapest_first(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 300, box_note="without adapter")
    offer(s, p, b, 200)
    body = get(client, f"/products/{p.id}").json()
    assert [(o["retailer"]["name"], o["price"], o["box_note"]) for o in body["offers"]] == [
        ("ShopB", 200, None), ("ShopA", 300, "without adapter")]


def test_orphan_detail_still_served(ctx, shops):
    client, s = ctx
    p = product(s, key="orphan")
    body = get(client, f"/products/{p.id}").json()
    assert body["offers"] == [] and body["listings"] == 0 and body["min_price"] is None


def test_product_prices_grouped_by_listing(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    la = offer(s, p, a, 300)
    offer(s, p, b, 200)
    s.add(PriceHistory(listing_id=la.id, price=280, availability="In stock"))
    s.flush()
    body = get(client, f"/products/{p.id}/prices").json()
    points = {l["retailer"]["name"]: [x["price"] for x in l["points"]] for l in body["listings"]}
    assert points == {"ShopA": [300, 280], "ShopB": [200]}


@pytest.mark.parametrize("path", ["/products/999999", "/products/999999/prices",
                                  "/compare/999999"])
def test_unknown_product_404(ctx, shops, path):
    client, _ = ctx
    assert get(client, path).status_code == 404


@pytest.mark.parametrize("path", ["/products/0", "/products/2147483648", "/compare/abc"])
def test_bad_ids_422(ctx, path):
    client, _ = ctx
    assert get(client, path).status_code == 422


# ---- /compare ---------------------------------------------------------------

def test_compare_best_offer_per_retailer(ctx, shops):
    client, s = ctx
    a, b, c = shops
    p = product(s)
    offer(s, p, a, 310), offer(s, p, a, 300), offer(s, p, b, 250)
    body = get(client, f"/compare/{p.id}").json()
    rows = [(r["retailer"]["name"], r["best"]["price"], r["offers"], r["cheapest_listed"])
            for r in body["retailers"]]
    assert rows == [("ShopB", 250, 1, True), ("ShopA", 300, 2, False)]
    assert body["spread"] == 50
    assert body["not_listed"] == ["ShopC"]


def test_compare_ties_all_marked(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 200), offer(s, p, b, 200)
    rows = get(client, f"/compare/{p.id}").json()["retailers"]
    assert [r["cheapest_listed"] for r in rows] == [True, True]


def test_compare_out_of_stock_never_cheapest(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 50, availability="Out of stock")
    offer(s, p, b, 300)
    body = get(client, f"/compare/{p.id}").json()
    rows = [(r["retailer"]["name"], r["cheapest_listed"]) for r in body["retailers"]]
    assert rows == [("ShopB", True), ("ShopA", False)]
    assert body["spread"] is None  # only one buyable offer


def test_compare_prefers_in_stock_listing_within_retailer(ctx, shops):
    client, s = ctx
    a = shops[0]
    p = product(s)
    offer(s, p, a, 50, availability="Out of stock")
    offer(s, p, a, 400)
    best = get(client, f"/compare/{p.id}").json()["retailers"][0]["best"]
    assert (best["price"], best["availability"]) == (400, "In stock")


def test_compare_single_retailer_has_no_spread(ctx, shops):
    client, s = ctx
    p = product(s)
    offer(s, p, shops[0], 100)
    body = get(client, f"/compare/{p.id}").json()
    assert body["spread"] is None and body["not_listed"] == ["ShopB", "ShopC"]


# ---- freshness: only listings from the retailer's latest, recent scrape ----

def test_listing_missing_from_latest_scrape_not_counted(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 50, days_ago=1)   # ShopA's old sighting, cheap
    offer(s, p, a, 300)              # ShopA's latest scrape
    offer(s, p, b, 250)
    item = get(client, "/products").json()["items"][0]
    assert (item["listings"], item["min_price"]) == (2, 250)
    rows = get(client, f"/compare/{p.id}").json()["retailers"]
    assert [(r["retailer"]["name"], r["best"]["price"], r["offers"]) for r in rows] == [
        ("ShopB", 250, 1), ("ShopA", 300, 1)]


def test_retailer_whose_scrape_is_old_drops_out(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 100, days_ago=5)  # ShopA has not been scraped for 5 days
    offer(s, p, b, 200)
    body = get(client, f"/compare/{p.id}").json()
    assert [r["retailer"]["name"] for r in body["retailers"]] == ["ShopB"]
    assert body["not_listed"] == ["ShopA", "ShopC"] and body["spread"] is None
    assert get(client, "/products", min_retailers=2).json()["total"] == 0


def test_same_scrape_run_spread_over_hours_is_current(ctx, shops):
    client, s = ctx
    a = shops[0]
    p = product(s)
    offer(s, p, a, 100)
    offer(s, p, a, 90, days_ago=2 / 24)  # saved two hours before the retailer's newest file
    assert get(client, "/products").json()["items"][0]["listings"] == 2


def test_product_with_only_old_listings_hidden_but_detail_marks_them(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 100, days_ago=5)
    other = product(s, key="other", name="Testco Other")
    offer(s, other, b, 1)
    assert [i["name"] for i in get(client, "/products").json()["items"]] == ["Testco Other"]
    body = get(client, f"/products/{p.id}").json()
    assert body["listings"] == 0 and body["min_price"] is None
    assert [(o["price"], o["current"]) for o in body["offers"]] == [(100, False)]


def test_detail_lists_current_offers_first(ctx, shops):
    client, s = ctx
    a, b, _ = shops
    p = product(s)
    offer(s, p, a, 50, days_ago=1)
    offer(s, p, a, 300)
    offer(s, p, b, 250)
    offers = get(client, f"/products/{p.id}").json()["offers"]
    assert [(o["price"], o["current"]) for o in offers] == [(250, True), (300, True), (50, False)]

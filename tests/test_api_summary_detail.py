import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.auth import require_user
from api.deps import get_session
from api.main import app
from db.models import Base, Listing, ListingCategory, PriceHistory, Retailer
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
    app.dependency_overrides[require_user] = lambda: None
    yield TestClient(app), session
    app.dependency_overrides.clear()
    session.close()
    trans.rollback()
    conn.close()


def add_retailer(session, name):
    retailer = Retailer(name=name, base_url="https://zqx.example")
    session.add(retailer)
    session.flush()
    return retailer


def add_listing(session, retailer, n, *, name=None, price=100,
                categories=(("Zqx Cat", "Zqx Type"),)):
    listing = Listing(
        retailer_id=retailer.id,
        url=f"https://zqx.example/{retailer.name}/{n}",
        name=name or f"Zqx item {n}",
        brand="ZqxBrand",
        brand_status="matched",
        brand_candidates=None,
        current_price=price,
        availability="In stock",
        taxonomy_version="1.0",
        brands_version="test",
    )
    for i, (category, product_type) in enumerate(categories):
        listing.categories.append(
            ListingCategory(
                category=category,
                product_type=product_type,
                mapping_status="mapped",
                raw_category="Zqx raw",
                raw_subcategory=f"sub{i}",
            )
        )
    session.add(listing)
    session.flush()
    return listing


def summary(client, **params):
    return client.get(f"{PREFIX}/listings/summary", params=params)


def by_retailer(response):
    return {r["retailer"]: r for r in response.json()["retailers"]}


# ---- /listings/summary ------------------------------------------------------

def test_summary_counts_min_max_and_cheapest(ctx):
    client, session = ctx
    a = add_retailer(session, "ZqxA")
    b = add_retailer(session, "ZqxB")
    add_listing(session, a, 1, price=300, name="Zqx widget one")
    cheap = add_listing(session, a, 2, price=100, name="Zqx widget two")
    add_listing(session, a, 3, price=200, name="Zqx widget three")
    add_listing(session, b, 4, price=250, name="Zqx widget four")

    response = summary(client, q="zqx widget")
    assert response.status_code == 200
    rows = by_retailer(response)
    assert response.json()["total"] == 4
    assert rows["ZqxA"]["listings"] == 3
    assert (rows["ZqxA"]["min_price"], rows["ZqxA"]["max_price"]) == (100, 300)
    assert rows["ZqxA"]["cheapest"] == {
        "id": cheap.id, "name": "Zqx widget two", "url": cheap.url, "price": 100,
    }
    assert rows["ZqxB"]["cheapest"]["price"] == 250


def test_summary_lists_every_retailer_even_with_no_matches(ctx):
    client, session = ctx
    a = add_retailer(session, "ZqxA")
    add_retailer(session, "ZqxEmpty")
    add_listing(session, a, 1, name="Zqx widget one")

    rows = by_retailer(summary(client, q="zqx widget"))
    assert rows["ZqxEmpty"] == {
        "retailer": "ZqxEmpty", "listings": 0,
        "min_price": None, "max_price": None, "cheapest": None,
    }


def test_summary_follows_the_filters(ctx):
    client, session = ctx
    a = add_retailer(session, "ZqxA")
    add_listing(session, a, 1, price=100, categories=(("Zqx Cat", "Zqx Type"),))
    add_listing(session, a, 2, price=200, categories=(("Zqx Cat", "Zqx Type"),))
    add_listing(session, a, 3, price=900, categories=(("Zqx Cat", "Zqx Other"),))

    rows = by_retailer(summary(client, retailer="ZqxA", product_type="Zqx Type"))
    assert rows["ZqxA"]["listings"] == 2 and rows["ZqxA"]["max_price"] == 200
    rows = by_retailer(summary(client, retailer="ZqxA", min_price=150))
    assert rows["ZqxA"]["listings"] == 2 and rows["ZqxA"]["min_price"] == 200


def test_summary_cheapest_tie_breaks_on_id(ctx):
    client, session = ctx
    a = add_retailer(session, "ZqxA")
    first = add_listing(session, a, 1, price=100, name="Zqx tie one")
    add_listing(session, a, 2, price=100, name="Zqx tie two")
    rows = by_retailer(summary(client, q="zqx tie"))
    assert rows["ZqxA"]["cheapest"]["id"] == first.id


def test_summary_with_no_matches(ctx):
    client, session = ctx
    add_retailer(session, "ZqxA")
    body = summary(client, q="no-such-product-zqx").json()
    assert body["total"] == 0
    assert all(r["listings"] == 0 and r["cheapest"] is None for r in body["retailers"])


def test_summary_rejects_inverted_price_range(ctx):
    client, _ = ctx
    assert summary(client, min_price=300, max_price=100).status_code == 422


# ---- /listings/{id} ---------------------------------------------------------

def test_detail_has_everything(ctx):
    client, session = ctx
    shop = add_retailer(session, "ZqxA")
    listing = add_listing(
        session, shop, 1, categories=(("CatA", "TypeA"), ("CatB", "TypeB"))
    )
    body = client.get(f"{PREFIX}/listings/{listing.id}").json()
    assert body["id"] == listing.id
    assert body["retailer"] == {"id": shop.id, "name": "ZqxA"}
    assert [c["product_type"] for c in body["categories"]] == ["TypeA", "TypeB"]
    assert body["taxonomy_version"] == "1.0" and body["brands_version"] == "test"
    assert body["first_seen_at"] and body["last_seen_at"]


def test_detail_missing_listing_is_404(ctx):
    client, _ = ctx
    assert client.get(f"{PREFIX}/listings/2000000000").status_code == 404


@pytest.mark.parametrize("bad", ["abc", "0", "-1", "2147483648"])
def test_detail_rejects_bad_ids(ctx, bad):
    client, _ = ctx
    assert client.get(f"{PREFIX}/listings/{bad}").status_code == 422


# ---- /listings/{id}/prices --------------------------------------------------

def test_prices_oldest_first(ctx):
    client, session = ctx
    shop = add_retailer(session, "ZqxA")
    listing = add_listing(session, shop, 1)
    for day, price in [(3, 90), (1, 100), (2, 95)]:
        listing.price_history.append(
            PriceHistory(
                price=price,
                availability="In stock",
                recorded_at=datetime(2026, 1, day, tzinfo=timezone.utc),
            )
        )
    session.flush()

    body = client.get(f"{PREFIX}/listings/{listing.id}/prices").json()
    assert body["listing_id"] == listing.id
    assert [p["price"] for p in body["points"]] == [100, 95, 90]


def test_prices_empty_history_is_ok(ctx):
    client, session = ctx
    listing = add_listing(session, add_retailer(session, "ZqxA"), 1)
    response = client.get(f"{PREFIX}/listings/{listing.id}/prices")
    assert response.status_code == 200 and response.json()["points"] == []


def test_prices_missing_listing_is_404(ctx):
    client, _ = ctx
    assert client.get(f"{PREFIX}/listings/2000000000/prices").status_code == 404


def test_prices_rejects_bad_id(ctx):
    client, _ = ctx
    assert client.get(f"{PREFIX}/listings/abc/prices").status_code == 422


def test_listing_routes_are_get_only(ctx):
    client, _ = ctx
    assert client.post(f"{PREFIX}/listings/1").status_code == 405
    assert client.post(f"{PREFIX}/listings/summary").status_code == 405

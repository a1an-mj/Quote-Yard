import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.deps import get_session
from api.main import app
from db.models import Base, Listing, ListingCategory, Retailer
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


def add_retailer(session, name, base_url=None):
    retailer = Retailer(name=name, base_url=base_url)
    session.add(retailer)
    session.flush()
    return retailer


def add_listing(session, retailer, n, *, brand="ZzBrand",
                categories=(("Zz Cat", "Zz Type"),)):
    listing = Listing(
        retailer_id=retailer.id,
        url=f"https://zz.example/{retailer.name}/{n}",
        name=f"Zz item {n}",
        brand=brand,
        brand_status="matched" if brand else "unknown",
        brand_candidates=None,
        current_price=100,
        availability="In stock",
        taxonomy_version="1.0",
        brands_version="test",
    )
    for i, (category, product_type) in enumerate(categories):
        listing.categories.append(
            ListingCategory(
                category=category,
                product_type=product_type,
                mapping_status="mapped" if product_type else "parent_only",
                raw_category="Zz raw",
                raw_subcategory=f"sub{i}",
            )
        )
    session.add(listing)
    session.flush()
    return listing


def test_retailers_show_counts_and_base_url(ctx):
    client, session = ctx
    shop = add_retailer(session, "ZzShop", "https://zz.example")
    add_retailer(session, "ZzEmpty")
    add_listing(session, shop, 1)
    add_listing(session, shop, 2)

    body = client.get(f"{PREFIX}/retailers").json()
    by_name = {r["name"]: r for r in body}
    assert by_name["ZzShop"]["listings"] == 2
    assert by_name["ZzShop"]["base_url"] == "https://zz.example"
    assert by_name["ZzEmpty"]["listings"] == 0


def test_retailer_counts_add_up_to_the_listings_table(ctx):
    client, session = ctx
    body = client.get(f"{PREFIX}/retailers").json()
    total = session.scalar(select(func.count()).select_from(Listing))
    assert sum(r["listings"] for r in body) == total


def test_product_types_count_distinct_listings_per_retailer(ctx):
    client, session = ctx
    a = add_retailer(session, "ZzShopA")
    b = add_retailer(session, "ZzShopB")
    # one listing with two category rows of the same type counts once
    add_listing(session, a, 1, categories=(("Zz Cat", "Zz Type"), ("Zz Cat", "Zz Type")))
    add_listing(session, a, 2)
    add_listing(session, b, 3)

    body = client.get(f"{PREFIX}/product-types").json()
    item = next(t for t in body if t["product_type"] == "Zz Type")
    assert item["category"] == "Zz Cat"
    assert item["listings"] == 3
    assert item["retailers"] == [
        {"retailer": "ZzShopA", "listings": 2},
        {"retailer": "ZzShopB", "listings": 1},
    ]


def test_product_types_skip_listings_without_a_type(ctx):
    client, session = ctx
    shop = add_retailer(session, "ZzShop")
    add_listing(session, shop, 1, categories=(("Zz Parent Only", None),))

    body = client.get(f"{PREFIX}/product-types").json()
    assert all(t["product_type"] for t in body)
    assert not any(t["category"] == "Zz Parent Only" for t in body)


def test_brands_exclude_unbranded_and_sort_by_count(ctx):
    client, session = ctx
    shop = add_retailer(session, "ZzShop")
    for n in range(3):
        add_listing(session, shop, n)
    add_listing(session, shop, 10, brand=None)

    body = client.get(f"{PREFIX}/brands").json()
    assert next(b for b in body if b["brand"] == "ZzBrand")["listings"] == 3
    assert all(b["brand"] for b in body)
    counts = [b["listings"] for b in body]
    assert counts == sorted(counts, reverse=True)


def test_catalog_is_get_only(ctx):
    client, _ = ctx
    assert client.post(f"{PREFIX}/retailers").status_code == 405

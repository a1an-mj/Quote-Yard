import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.deps import get_session
from api.main import app
from db.models import Base, Listing, ListingCategory, Retailer
from db.session import get_engine

PREFIX = "/api/v1"
SHOP = "ZqxShop"


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
def shop(ctx):
    _, session = ctx
    retailer = Retailer(name=SHOP, base_url="https://zqx.example")
    session.add(retailer)
    session.flush()
    return retailer


def add_listing(session, retailer, n, *, name=None, price=100, availability="In stock",
                brand="ZqxBrand", candidates=None, last_seen=None,
                categories=(("Zqx Cat", "Zqx Type"),)):
    status = "review" if candidates else ("matched" if brand else "unknown")
    if candidates:
        brand = None
    listing = Listing(
        retailer_id=retailer.id,
        url=f"https://zqx.example/{n}",
        name=name or f"Zqx item {n}",
        brand=brand,
        brand_status=status,
        brand_candidates=candidates,
        current_price=price,
        availability=availability,
        taxonomy_version="1.0",
        brands_version="test",
    )
    if last_seen:
        listing.last_seen_at = last_seen
    for i, (category, product_type) in enumerate(categories):
        listing.categories.append(
            ListingCategory(
                category=category,
                product_type=product_type,
                mapping_status="mapped" if product_type else "parent_only",
                raw_category="Zqx raw",
                raw_subcategory=f"sub{i}",
            )
        )
    session.add(listing)
    session.flush()
    return listing


def get(client, **params):
    params.setdefault("retailer", SHOP)
    return client.get(f"{PREFIX}/listings", params=params)


def names(response):
    return [item["name"] for item in response.json()["items"]]


def test_page_shape_and_defaults(ctx, shop):
    client, session = ctx
    for n in (1, 2, 3):
        add_listing(session, shop, n)
    body = get(client).json()
    assert (body["total"], body["limit"], body["offset"]) == (3, 20, 0)
    assert len(body["items"]) == 3
    item = body["items"][0]
    assert item["retailer"]["name"] == SHOP
    assert item["brand"] == "ZqxBrand" and item["brand_status"] == "matched"
    assert item["brand_candidates"] is None
    assert item["availability"] == "In stock" and isinstance(item["price"], int)
    assert item["categories"][0]["product_type"] == "Zqx Type"


def test_pagination_walks_the_results(ctx, shop):
    client, session = ctx
    for n in range(1, 6):
        add_listing(session, shop, n)
    pages = [get(client, sort="name", limit=2, offset=o) for o in (0, 2, 4)]
    walked = [name for page in pages for name in names(page)]
    assert walked == [f"Zqx item {n}" for n in range(1, 6)]
    assert pages[0].json()["total"] == 5
    assert pages[2].json()["offset"] == 4 and len(pages[2].json()["items"]) == 1


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_paging_limits_are_validated(ctx, shop, params):
    client, _ = ctx
    assert get(client, **params).status_code == 422


def test_q_requires_every_word_ignoring_case(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, name="Zqx Galaxy S25 Ultra 256GB")
    add_listing(session, shop, 2, name="Zqx Galaxy A07 128GB")
    add_listing(session, shop, 3, name="Zqx Pixel 9")
    assert names(get(client, q="galaxy s25")) == ["Zqx Galaxy S25 Ultra 256GB"]
    assert get(client, q="galaxy").json()["total"] == 2
    assert get(client, q="GALAXY   s25 ").json()["total"] == 1
    assert get(client, q="galaxy pixel").json()["total"] == 0


def test_q_wildcards_are_matched_literally(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, name="Zqx 50% off")
    add_listing(session, shop, 2, name="Zqx 500 off")
    add_listing(session, shop, 3, name="Zqx a_b")
    add_listing(session, shop, 4, name="Zqx axb")
    assert names(get(client, q="50%")) == ["Zqx 50% off"]
    assert names(get(client, q="a_b")) == ["Zqx a_b"]


def test_retailer_filter_ignores_case(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1)
    assert get(client, retailer="zqxSHOP").json()["total"] == 1
    assert get(client, retailer="NoSuchShop").json()["total"] == 0


def test_product_type_filter_returns_each_listing_once(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, categories=(("Zqx Cat", "Zqx Type"), ("Zqx Cat", "Zqx Type")))
    add_listing(session, shop, 2, categories=(("Zqx Other", "Zqx Other Type"),))
    body = get(client, product_type="zqx type").json()
    assert body["total"] == 1 and len(body["items"]) == 1
    assert len(body["items"][0]["categories"]) == 2


def test_category_and_type_must_match_the_same_row(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, categories=(("CatA", "TypeA"), ("CatB", "TypeB")))
    assert get(client, category="CatA", product_type="TypeA").json()["total"] == 1
    assert get(client, category="CatA", product_type="TypeB").json()["total"] == 0


def test_brand_filter(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, brand="ZqxBrand")
    add_listing(session, shop, 2, brand="OtherBrand")
    add_listing(session, shop, 3, brand=None)
    assert get(client, brand="zqxbrand").json()["total"] == 1


def test_price_range(ctx, shop):
    client, session = ctx
    for n, price in enumerate([100, 200, 300], start=1):
        add_listing(session, shop, n, price=price)
    assert get(client, min_price=150).json()["total"] == 2
    assert get(client, max_price=250).json()["total"] == 2
    assert get(client, min_price=150, max_price=250).json()["total"] == 1


def test_min_price_above_max_price_is_rejected(ctx, shop):
    client, _ = ctx
    assert get(client, min_price=300, max_price=100).status_code == 422


def test_availability_filter_and_validation(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, availability="In stock")
    add_listing(session, shop, 2, availability="Unknown")
    assert get(client, availability="Unknown").json()["total"] == 1
    assert get(client, availability="Maybe").status_code == 422


def test_sorting_with_stable_ties(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, price=300, name="Zqx b")
    add_listing(session, shop, 2, price=100, name="Zqx c")
    add_listing(session, shop, 3, price=100, name="Zqx a")
    assert names(get(client, sort="price_asc")) == ["Zqx c", "Zqx a", "Zqx b"]
    assert names(get(client, sort="price_desc")) == ["Zqx b", "Zqx c", "Zqx a"]
    assert names(get(client, sort="name")) == ["Zqx a", "Zqx b", "Zqx c"]
    assert get(client, sort="bogus").status_code == 422


def test_seen_since(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, last_seen=datetime(2020, 1, 1, tzinfo=timezone.utc))
    add_listing(session, shop, 2)
    assert get(client, seen_since="2024-01-01T00:00:00Z").json()["total"] == 1
    assert get(client, seen_since="2019-01-01T00:00:00Z").json()["total"] == 2


def test_review_listing_exposes_its_candidates(ctx, shop):
    client, session = ctx
    add_listing(session, shop, 1, candidates=["Faber", "LG"])
    item = get(client).json()["items"][0]
    assert item["brand"] is None and item["brand_status"] == "review"
    assert item["brand_candidates"] == ["Faber", "LG"]


def test_overlong_query_is_rejected(ctx, shop):
    client, _ = ctx
    assert get(client, q="x" * 101).status_code == 422


def test_listings_is_get_only(ctx):
    client, _ = ctx
    assert client.post(f"{PREFIX}/listings").status_code == 405

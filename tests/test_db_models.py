import sys
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.models import Base, Listing, ListingCategory, PriceHistory, Retailer
from db.session import get_engine


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
def session(engine):
    conn = engine.connect()
    trans = conn.begin()
    s = Session(bind=conn, join_transaction_mode="create_savepoint")
    yield s
    s.close()
    trans.rollback()
    conn.close()


def make_listing(retailer, url="https://x/1", **overrides):
    fields = dict(
        retailer_id=retailer.id,
        url=url,
        name="Samsung Galaxy A07",
        brand="Samsung",
        brand_status="matched",
        brand_candidates=None,
        current_price=13499,
        availability="In stock",
        taxonomy_version="1.0",
        brands_version="1.1",
    )
    fields.update(overrides)
    return Listing(**fields)


@pytest.fixture
def retailer(session):
    r = Retailer(name="TestShop")
    session.add(r)
    session.flush()
    return r


def test_valid_listing_with_history_and_category(session, retailer):
    listing = make_listing(retailer)
    listing.categories.append(
        ListingCategory(
            category="Mobiles & Tablets", product_type="Mobile Phone",
            mapping_status="mapped", raw_category="Mobiles", raw_subcategory=None,
        )
    )
    listing.price_history.append(PriceHistory(price=13499, availability="In stock"))
    session.add(listing)
    session.flush()
    assert listing.id is not None


def test_duplicate_retailer_url_rejected(session, retailer):
    session.add(make_listing(retailer))
    session.flush()
    session.add(make_listing(retailer))
    with pytest.raises(IntegrityError):
        session.flush()


def test_bad_availability_rejected(session, retailer):
    session.add(make_listing(retailer, availability="Maybe"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_zero_price_rejected(session, retailer):
    session.add(make_listing(retailer, current_price=0))
    with pytest.raises(IntegrityError):
        session.flush()


def test_review_requires_candidates_and_null_brand(session, retailer):
    ok = make_listing(
        retailer, url="https://x/ok", brand=None,
        brand_status="review", brand_candidates=["Faber", "LG"],
    )
    session.add(ok)
    session.flush()
    session.add(make_listing(retailer, url="https://x/bad", brand_status="review"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_null_subcategory_duplicate_rejected(session, retailer):
    listing = make_listing(retailer)
    session.add(listing)
    session.flush()
    for _ in range(2):
        session.add(
            ListingCategory(
                listing_id=listing.id, category=None, product_type=None,
                mapping_status="unmapped", raw_category="Gadgets",
                raw_subcategory=None,
            )
        )
    with pytest.raises(IntegrityError):
        session.flush()
import sys
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.loader import LoadError, build_batch, load_batch, validate_entries
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
    s.add(Retailer(name="TestShop"))
    s.flush()
    yield s
    s.close()
    trans.rollback()
    conn.close()


def rec(**over):
    base = dict(
        shop="TestShop", url="https://x/1", name="Samsung Galaxy A07",
        price=13499, availability="In stock",
        brand="Samsung", brand_status="matched", brand_candidates=None,
        category="Mobiles & Tablets", product_type="Mobile Phone",
        mapping_status="mapped", raw_category="Mobiles", raw_subcategory=None,
        taxonomy_version="1.0",
    )
    base.update(over)
    return base


def run(session, *records):
    entries = [("test", r) for r in records]
    validate_entries(entries, {"TestShop"})
    batch, warnings = build_batch(entries)
    stats = load_batch(session, batch, "1.1")
    return stats, warnings


def history_count(session):
    return session.scalar(
        select(func.count()).select_from(PriceHistory)
        .join(Listing).join(Retailer).where(Retailer.name == "TestShop")
    )


def get_listing(session, url="https://x/1"):
    return session.scalar(select(Listing).where(Listing.url == url))


def test_first_load(session):
    stats, _ = run(session, rec())
    assert stats["listings_inserted"] == 1
    assert stats["categories_inserted"] == 1
    assert stats["history_rows"] == 1
    assert history_count(session) == 1


def test_rerun_adds_nothing(session):
    run(session, rec())
    stats, _ = run(session, rec())
    assert stats["listings_inserted"] == 0
    assert stats["listings_updated"] == 1
    assert stats["categories_inserted"] == 0
    assert stats["history_rows"] == 0
    assert history_count(session) == 1


def test_price_change_adds_history(session):
    run(session, rec())
    stats, _ = run(session, rec(price=12999))
    assert stats["history_rows"] == 1
    assert history_count(session) == 2
    assert get_listing(session).current_price == 12999


def test_unknown_availability_is_not_a_change(session):
    run(session, rec())                                  # In stock: row 1
    run(session, rec(availability="Unknown"))            # no row
    assert history_count(session) == 1
    assert get_listing(session).availability == "Unknown"
    run(session, rec(availability="In stock"))           # same as last known
    assert history_count(session) == 1
    run(session, rec(availability="Out of stock"))       # real change
    assert history_count(session) == 2


def test_duplicate_url_first_wins_and_merges_categories(session):
    a = rec(price=100, raw_category="Home Theater", product_type="Soundbar")
    b = rec(price=200, raw_category="Sound Bars", product_type="Soundbar")
    stats, warnings = run(session, a, b)
    assert stats["listings_inserted"] == 1
    assert stats["categories_inserted"] == 2
    assert len(warnings) == 1
    assert get_listing(session).current_price == 100


def test_same_pair_twice_is_one_category(session):
    stats, warnings = run(session, rec(), rec())
    assert stats["categories_inserted"] == 1
    assert warnings == []


def test_remapping_updates_category(session):
    run(session, rec())
    stats, _ = run(session, rec(category="Other", product_type=None,
                                mapping_status="parent_only"))
    assert stats["categories_updated"] == 1
    cats = session.scalars(select(ListingCategory)).all()
    cats = [c for c in cats if c.listing_id == get_listing(session).id]
    assert len(cats) == 1 and cats[0].mapping_status == "parent_only"


def test_review_record_stores_candidates(session):
    run(session, rec(brand=None, brand_status="review",
                     brand_candidates=["Faber", "LG"]))
    listing = get_listing(session)
    assert listing.brand is None and listing.brand_candidates == ["Faber", "LG"]


def test_unknown_shop_fails():
    with pytest.raises(LoadError):
        validate_entries([("t", rec(shop="Nope"))], {"TestShop"})


@pytest.mark.parametrize("bad", [
    dict(availability="Maybe"),
    dict(price=0),
    dict(price="100"),
    dict(url="not-a-url"),
    dict(brand_status="matched", brand=None),
    dict(brand_status="review", brand=None, brand_candidates=None),
    dict(raw_category=""),
])
def test_bad_records_fail(bad):
    with pytest.raises(LoadError):
        validate_entries([("t", rec(**bad))], {"TestShop"})
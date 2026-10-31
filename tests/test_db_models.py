import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.models import (
    Base,
    CanonicalProduct,
    EmailCode,
    Listing,
    ListingCategory,
    PriceHistory,
    Retailer,
    User,
    UserSession,
)
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

# ---- Phase 5: canonical products -------------------------------------------

def make_product(**overrides):
    fields = dict(
        brand="Samsung", name="Samsung Galaxy A07 5G [4 GB RAM, 128 GB]",
        category="Mobiles & Tablets", product_type="Mobile Phone",
        model="a07", network="5G", ram_gb=4, storage_gb=128, package=None,
        ta_code=None, match_key="testco|zed9|5g|4|128|", matching_version="1.1",
    )
    fields.update(overrides)
    return CanonicalProduct(**fields)


def test_product_links_listings_with_box_note(session, retailer):
    product = make_product()
    a = make_listing(retailer, url="https://x/a", canonical_product=product)
    b = make_listing(retailer, url="https://x/b", canonical_product=product,
                     box_note="without adapter")
    session.add_all([a, b])
    session.flush()
    assert {l.box_note for l in product.listings} == {None, "without adapter"}
    assert a.canonical_product_id == b.canonical_product_id == product.id


def test_feature_phone_product_keyed_on_ta_code(session):
    session.add(make_product(
        brand="Nokia", model="110 power keypad", network=None, ram_gb=None,
        storage_gb=None, ta_code="TA-0000", match_key="testco|ta|ta-0000"))
    session.flush()


def test_duplicate_match_key_rejected(session):
    session.add(make_product())
    session.flush()
    session.add(make_product(name="other name"))
    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("overrides", [
    {"storage_gb": None},                    # no storage and no TA code
    {"network": "6G"},
    {"ram_gb": 0},
    {"storage_gb": 0},
    {"brand": None},
])
def test_bad_product_rejected(session, overrides):
    session.add(make_product(**overrides))
    with pytest.raises(IntegrityError):
        session.flush()


# ---- accounts ---------------------------------------------------------------

def make_user(email="a@example.com"):
    return User(email=email, password_hash="x", first_name="T")


def test_duplicate_email_rejected(session):
    session.add(make_user())
    session.flush()
    session.add(make_user())
    with pytest.raises(IntegrityError):
        session.flush()


def test_mixed_case_email_rejected(session):
    session.add(make_user("A@Example.com"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_bad_code_purpose_rejected(session):
    user = make_user()
    session.add(user)
    session.flush()
    session.add(EmailCode(user_id=user.id, purpose="other", code_hash="h",
                          expires_at=datetime.now(timezone.utc)))
    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_user_removes_codes_and_sessions(session):
    user = make_user()
    session.add(user)
    session.flush()
    now = datetime.now(timezone.utc)
    session.add_all([
        EmailCode(user_id=user.id, purpose="verify_email", code_hash="h", expires_at=now),
        UserSession(user_id=user.id, token_hash="t", expires_at=now),
    ])
    session.flush()
    session.delete(user)
    session.flush()
    session.expire_all()
    assert session.scalars(select(EmailCode).where(EmailCode.code_hash == "h")).first() is None
    assert session.scalars(select(UserSession).where(UserSession.token_hash == "t")).first() is None

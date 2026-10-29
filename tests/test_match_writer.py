import sys
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db.match_writer import write_matches
from matching.phone_matcher import MATCHING_VERSION
from db.models import Base, CanonicalProduct, Listing, ListingCategory, Retailer
from db.session import get_engine

SHOPS = {"ShopA", "ShopB"}


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
    s.add_all([Retailer(name=n) for n in sorted(SHOPS)])
    s.flush()
    yield s
    s.close()
    trans.rollback()
    conn.close()


def add(session, shop, name, url=None, price=20000, brand="Testco",
        product_type="Mobile Phone", status="matched"):
    rid = session.scalar(select(Retailer.id).where(Retailer.name == shop))
    listing = Listing(
        retailer_id=rid, url=url or f"https://{shop}/{name}", name=name,
        brand=brand if status == "matched" else None, brand_status=status,
        brand_candidates=["Testco", "Other"] if status == "review" else None,
        current_price=price, availability="In stock",
        taxonomy_version="1.0", brands_version="1.1",
    )
    listing.categories.append(ListingCategory(
        category="Mobiles & Tablets", product_type=product_type,
        mapping_status="mapped", raw_category="Mobiles"))
    session.add(listing)
    session.flush()
    return listing


def run(session):
    return write_matches(session, retailers=SHOPS)


def product_of(session, listing):
    session.refresh(listing)
    if listing.canonical_product_id is None:
        return None
    return session.get(CanonicalProduct, listing.canonical_product_id)


def test_cross_retailer_group_written_and_linked(session):
    a = add(session, "ShopA", "Testco Zed 9 5G (Black, 128 GB) (8 GB RAM)")
    b = add(session, "ShopB", "Testco Zed 9 5G | 8 GB | 128 GB | Blue")
    stats = run(session)
    assert stats["products_inserted"] == 1 and stats["listings_linked"] == 2
    p = product_of(session, a)
    assert p is not None and p == product_of(session, b)
    assert (p.brand, p.model, p.network, p.ram_gb, p.storage_gb) == ("Testco", "zed 9", "5G", 8, 128)
    assert p.match_key == "testco|zed9|5g|8|128|"
    assert (p.category, p.product_type, p.matching_version) == (
        "Mobiles & Tablets", "Mobile Phone", MATCHING_VERSION)


def test_rerun_changes_nothing(session):
    add(session, "ShopA", "Testco Zed 9 5G (Black, 128 GB) (8 GB RAM)")
    add(session, "ShopB", "Testco Zed 9 5G | 8 GB | 128 GB | Blue")
    run(session)
    stats = run(session)
    for key in ("products_inserted", "products_updated", "listings_linked",
                "listings_relinked", "listings_unlinked", "box_notes_changed"):
        assert stats.get(key, 0) == 0, key


def test_box_note_written(session):
    a = add(session, "ShopA", "Testco Zed 9 5G Without Adapter (Black, 128 GB) (8 GB RAM)")
    b = add(session, "ShopB", "Testco Zed 9 5G | 8 GB | 128 GB | Blue")
    stats = run(session)
    assert stats["box_notes_changed"] == 1
    session.refresh(a), session.refresh(b)
    assert (a.box_note, b.box_note) == ("without adapter", None)
    assert a.canonical_product_id == b.canonical_product_id


def test_untrusted_and_partial_listings_stay_unlinked(session):
    r = add(session, "ShopA", "Testco Zed 9 (8+128GB)", status="review")
    p = add(session, "ShopB", "Testco Zed 9 | 128 GB | Blue")  # no RAM
    stats = run(session)
    assert stats["skipped"] == 2 and stats.get("products_inserted", 0) == 0
    assert product_of(session, r) is None and product_of(session, p) is None


def test_other_product_types_untouched(session):
    tv = add(session, "ShopA", "Testco 43 inch TV | 8 GB | 128 GB", product_type="Television")
    stats = run(session)
    assert stats["listings_in_scope"] == 0
    assert product_of(session, tv) is None


def test_existing_product_reused_and_updated(session):
    a = add(session, "ShopA", "Testco Zed 9 5G (Black, 128 GB) (8 GB RAM)")
    run(session)
    pid = a.canonical_product_id
    session.get(CanonicalProduct, pid).name = "stale name"
    session.flush()
    stats = run(session)
    assert stats["products_updated"] == 1 and stats.get("products_inserted", 0) == 0
    assert product_of(session, a).id == pid


def test_listing_that_no_longer_matches_is_unlinked_product_kept(session):
    a = add(session, "ShopA", "Testco Zed 9 5G (Black, 128 GB) (8 GB RAM)")
    run(session)
    pid = a.canonical_product_id
    a.brand, a.brand_status, a.brand_candidates = None, "review", ["Testco", "Other"]
    session.flush()
    stats = run(session)
    assert stats["listings_unlinked"] == 1
    assert product_of(session, a) is None
    assert session.get(CanonicalProduct, pid) is not None  # never deleted


def test_relinked_when_specs_change(session):
    a = add(session, "ShopA", "Testco Zed 9 5G (Black, 128 GB) (8 GB RAM)")
    run(session)
    first = a.canonical_product_id
    a.name = "Testco Zed 9 5G (Black, 256 GB) (8 GB RAM)"
    session.flush()
    stats = run(session)
    assert stats["listings_relinked"] == 1 and stats["products_inserted"] == 1
    assert product_of(session, a).id != first

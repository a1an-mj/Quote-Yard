"""
Quote Yard - Phase 5 match writer.

Runs the phone matcher over the listings already in PostgreSQL and writes
the result: one canonical_products row per group, and canonical_product_id
plus box_note on each listing.

Usage (from the repo root):
    python -m db.match_writer --dry-run    # match and report, write nothing
    python -m db.match_writer              # write

Rules:
- Input is the database, not the JSON files, so matches always describe
  the loaded listings. Scope: listings with a category row whose
  product_type is "Mobile Phone". Listings outside the scope are never
  touched.
- One transaction: all or nothing.
- canonical_products are upserted by match_key. They are never deleted:
  a product left with no listings (after a rule change) is reported as
  orphaned, so product ids stay stable.
- In-scope listings the matcher skips or sends to review get
  canonical_product_id = NULL; box_note is set on every in-scope listing.
- Idempotent: a rerun on unchanged data changes nothing.
"""

from __future__ import annotations

import argparse
from collections import Counter

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from db.models import CanonicalProduct, Listing, ListingCategory, Retailer
from db.session import get_engine
from matching.phone_matcher import MATCHING_VERSION, match

PRODUCT_TYPE = "Mobile Phone"
PRODUCT_FIELDS = ("brand", "name", "model", "network", "ram_gb", "storage_gb",
                  "package", "ta_code")


def collect_records(session: Session, product_type: str = PRODUCT_TYPE,
                    retailers: set[str] | None = None) -> tuple[list[dict], dict]:
    """Return (matcher records, listing by id) for the in-scope listings."""
    in_type = exists().where(
        ListingCategory.listing_id == Listing.id,
        ListingCategory.product_type == product_type,
    )
    query = select(Listing, Retailer.name).join(Retailer).where(in_type).order_by(Listing.id)
    if retailers is not None:
        query = query.where(Retailer.name.in_(retailers))

    records, listings = [], {}
    for listing, shop in session.execute(query):
        listings[listing.id] = listing
        records.append({
            "listing_id": listing.id, "shop": shop, "url": listing.url,
            "name": listing.name, "price": listing.current_price,
            "brand": listing.brand, "brand_status": listing.brand_status,
        })
    return records, listings


def _category_for(session: Session, listing_ids: list[int], product_type: str) -> str | None:
    rows = session.scalars(
        select(ListingCategory.category).where(
            ListingCategory.listing_id.in_(listing_ids),
            ListingCategory.product_type == product_type,
        )
    )
    counts = Counter(c for c in rows if c)
    return min(counts, key=lambda c: (-counts[c], c)) if counts else None


def write_matches(session: Session, product_type: str = PRODUCT_TYPE,
                  retailers: set[str] | None = None) -> dict:
    records, listings = collect_records(session, product_type, retailers)
    by_url = {(r["shop"], r["url"]): r["listing_id"] for r in records}
    groups, review, skipped = match(records)

    stats = Counter()
    stats.update(listings_in_scope=len(records), groups=len(groups),
                 cross_retailer=sum(len(g["shops"]) >= 2 for g in groups),
                 review_items=len(review), skipped=len(skipped))

    existing = {p.match_key: p for p in session.scalars(
        select(CanonicalProduct).where(
            CanonicalProduct.match_key.in_([g["match_key"] for g in groups])))}

    target: dict[int, tuple[CanonicalProduct | None, str | None]] = {}
    for g in groups:
        ids = [by_url[(m["shop"], m["url"])] for m in g["listings"]]
        values = {f: g[f] for f in PRODUCT_FIELDS}
        values.update(category=_category_for(session, ids, product_type),
                      product_type=product_type, matching_version=MATCHING_VERSION)
        product = existing.get(g["match_key"])
        if product is None:
            product = CanonicalProduct(match_key=g["match_key"], **values)
            session.add(product)
            stats["products_inserted"] += 1
        elif any(getattr(product, k) != v for k, v in values.items()):
            for k, v in values.items():
                setattr(product, k, v)
            stats["products_updated"] += 1
        for m, lid in zip(g["listings"], ids):
            target[lid] = (product, m["box_note"])

    for item in review:
        for m in item["listings"]:
            lid = by_url[(m["shop"], m["url"])]
            target.setdefault(lid, (None, m["box_note"]))
    for m in skipped:
        target.setdefault(by_url[(m["shop"], m["url"])], (None, m["box_note"]))

    session.flush()  # new products get ids
    for lid, listing in listings.items():
        product, box_note = target.get(lid, (None, None))
        new_id = product.id if product is not None else None
        if listing.canonical_product_id != new_id:
            if new_id is None:
                stats["listings_unlinked"] += 1
            elif listing.canonical_product_id is None:
                stats["listings_linked"] += 1
            else:
                stats["listings_relinked"] += 1
            listing.canonical_product_id = new_id
        if listing.box_note != box_note:
            listing.box_note = box_note
            stats["box_notes_changed"] += 1
    session.flush()

    linked = exists().where(Listing.canonical_product_id == CanonicalProduct.id)
    stats["orphaned_products"] = session.scalar(
        select(func.count()).select_from(CanonicalProduct)
        .where(CanonicalProduct.product_type == product_type, ~linked)
    )
    return dict(stats)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="do everything, then roll back")
    args = parser.parse_args()

    with Session(get_engine()) as session:
        stats = write_matches(session)
        if args.dry_run:
            session.rollback()
        else:
            session.commit()
        counts = {
            "canonical_products": session.scalar(
                select(func.count()).select_from(CanonicalProduct)),
            "linked_listings": session.scalar(
                select(func.count()).select_from(Listing)
                .where(Listing.canonical_product_id.is_not(None))),
        }

    print("DRY RUN (rolled back)" if args.dry_run else "WRITTEN")
    print(f"  matching_version:      {MATCHING_VERSION}")
    keys = ("listings_in_scope", "groups", "cross_retailer", "review_items", "skipped",
            "products_inserted", "products_updated", "listings_linked",
            "listings_relinked", "listings_unlinked", "box_notes_changed",
            "orphaned_products")
    for key in keys:
        print(f"  {key + ':':<22} {stats.get(key, 0)}")
    print(f"Database now: {counts}")


if __name__ == "__main__":
    main()

"""
Quote Yard - Phase 3 loader.

Reads branded_data/*.json and loads it into PostgreSQL.

Usage (from the repo root):
    python -m db.loader --dry-run     # validate and report, write nothing
    python -m db.loader               # load

Rules:
- Everything is validated before anything is written, and the load is one
  transaction: all or nothing.
- Files are read in sorted filename order, records in file order. Records
  are deduped by (shop, url); the FIRST record in load order wins. A warning
  is logged if a later duplicate has a different name or price.
- Every distinct (raw_category, raw_subcategory) seen for a URL becomes one
  listing_categories row.
- Price history: a row on first sighting, on any price change, and when a
  KNOWN availability differs from the last known availability. "Unknown" is
  never treated as a change.
- Listings are never deleted. An unknown shop fails the load.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from db.models import (
    AVAILABILITY_VALUES,
    BRAND_STATUSES,
    MAPPING_STATUSES,
    Listing,
    ListingCategory,
    PriceHistory,
    Retailer,
)
from db.session import get_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRANDED_DIR = PROJECT_ROOT / "branded_data"
BRANDS_FILE = PROJECT_ROOT / "data_processing" / "brands.json"

Entry = tuple[str, dict]  # (where, record)


class LoadError(ValueError):
    """The input data cannot be loaded."""


def clean_sub(value) -> str | None:
    """Empty or blank subcategories become None."""
    return (value or "").strip() or None


def read_entries(input_dir: Path) -> list[Entry]:
    files = sorted(input_dir.glob("*.json"))
    if not files:
        raise LoadError(f"No JSON files in {input_dir}")
    entries: list[Entry] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise LoadError(f"Expected a list of records in {path}")
        for index, record in enumerate(data):
            entries.append((f"{path.name}[{index}]", record))
    return entries


def validate_entries(entries: list[Entry], known_shops: set[str]) -> None:
    errors: list[str] = []

    for where, rec in entries:
        problems = []
        if rec.get("shop") not in known_shops:
            problems.append(f"unknown shop {rec.get('shop')!r}")
        url = rec.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            problems.append(f"bad url {url!r}")
        if not rec.get("name"):
            problems.append("missing name")
        price = rec.get("price")
        if not isinstance(price, int) or isinstance(price, bool) or price <= 0:
            problems.append(f"bad price {price!r}")
        if rec.get("availability") not in AVAILABILITY_VALUES:
            problems.append(f"bad availability {rec.get('availability')!r}")
        if rec.get("mapping_status") not in MAPPING_STATUSES:
            problems.append(f"bad mapping_status {rec.get('mapping_status')!r}")
        if not rec.get("raw_category"):
            problems.append("missing raw_category")
        if not rec.get("taxonomy_version"):
            problems.append("missing taxonomy_version")

        status = rec.get("brand_status")
        brand = rec.get("brand")
        candidates = rec.get("brand_candidates")
        if status not in BRAND_STATUSES:
            problems.append(f"bad brand_status {status!r}")
        else:
            if (status == "matched") != (brand is not None):
                problems.append("brand must be set exactly when status is matched")
            if (status == "review") != (candidates is not None):
                problems.append("brand_candidates must be set exactly when status is review")
            if status == "review" and (
                not isinstance(candidates, list) or len(candidates) < 2
            ):
                problems.append("review needs a list of 2+ candidates")

        if problems:
            errors.append(f"{where}: " + "; ".join(problems))

    if errors:
        shown = "\n  ".join(errors[:20])
        more = f"\n  ... and {len(errors) - 20} more" if len(errors) > 20 else ""
        raise LoadError(f"{len(errors)} invalid record(s):\n  {shown}{more}")


def build_batch(entries: list[Entry]) -> tuple[dict, list[str]]:
    """Dedupe by (shop, url). First record wins; categories are merged."""
    batch: dict[tuple[str, str], dict] = {}
    warnings: list[str] = []

    for where, rec in entries:
        key = (rec["shop"], rec["url"])
        pair = (rec["raw_category"].strip(), clean_sub(rec.get("raw_subcategory")))
        slot = batch.get(key)
        if slot is None:
            batch[key] = {"record": rec, "where": where, "pairs": {pair: rec}}
            continue
        first = slot["record"]
        if rec["name"] != first["name"] or rec["price"] != first["price"]:
            warnings.append(
                f"{where}: duplicate of {slot['where']} ({rec['shop']}) differs "
                f"in name or price; keeping the first"
            )
        slot["pairs"].setdefault(pair, rec)

    return batch, warnings


def _needs_history(session: Session, listing_id: int, price: int, availability: str) -> bool:
    ordering = (PriceHistory.recorded_at.desc(), PriceHistory.id.desc())
    last = session.execute(
        select(PriceHistory.price)
        .where(PriceHistory.listing_id == listing_id)
        .order_by(*ordering)
        .limit(1)
    ).first()
    if last is None:
        return True
    if price != last.price:
        return True
    if availability == "Unknown":
        return False
    last_known = session.scalar(
        select(PriceHistory.availability)
        .where(
            PriceHistory.listing_id == listing_id,
            PriceHistory.availability != "Unknown",
        )
        .order_by(*ordering)
        .limit(1)
    )
    return availability != last_known


def load_batch(session: Session, batch: dict, brands_version: str) -> dict:
    retailers = {r.name: r.id for r in session.scalars(select(Retailer))}
    existing = {
        (l.retailer_id, l.url): l
        for l in session.scalars(
            select(Listing)
            .where(Listing.retailer_id.in_(set(retailers.values())))
            .options(selectinload(Listing.categories))
        )
    }

    stats = {
        "listings_inserted": 0,
        "listings_updated": 0,
        "categories_inserted": 0,
        "categories_updated": 0,
        "history_rows": 0,
    }

    for (shop, url), slot in batch.items():
        rec = slot["record"]
        retailer_id = retailers[shop]
        fields = dict(
            name=rec["name"],
            brand=rec["brand"],
            brand_status=rec["brand_status"],
            brand_candidates=rec["brand_candidates"],
            current_price=rec["price"],
            availability=rec["availability"],
            taxonomy_version=rec["taxonomy_version"],
            brands_version=brands_version,
        )

        listing = existing.get((retailer_id, url))
        if listing is None:
            listing = Listing(retailer_id=retailer_id, url=url, **fields)
            session.add(listing)
            stats["listings_inserted"] += 1
            record_history = True
        else:
            record_history = _needs_history(
                session, listing.id, rec["price"], rec["availability"]
            )
            for key, value in fields.items():
                setattr(listing, key, value)
            listing.last_seen_at = func.now()
            stats["listings_updated"] += 1

        if record_history:
            row = PriceHistory(price=rec["price"], availability=rec["availability"])
            if listing.id is None:
                listing.price_history.append(row)
            else:
                row.listing_id = listing.id
                session.add(row)
            stats["history_rows"] += 1

        by_pair = {(c.raw_category, c.raw_subcategory or ""): c for c in listing.categories}
        for (raw_category, raw_subcategory), prec in slot["pairs"].items():
            values = dict(
                category=prec.get("category"),
                product_type=prec.get("product_type"),
                mapping_status=prec["mapping_status"],
            )
            current = by_pair.get((raw_category, raw_subcategory or ""))
            if current is None:
                listing.categories.append(
                    ListingCategory(
                        raw_category=raw_category,
                        raw_subcategory=raw_subcategory,
                        **values,
                    )
                )
                stats["categories_inserted"] += 1
            elif any(getattr(current, k) != v for k, v in values.items()):
                for key, value in values.items():
                    setattr(current, key, value)
                stats["categories_updated"] += 1

    session.flush()
    return stats


def _brands_version() -> str:
    config = json.loads(BRANDS_FILE.read_text(encoding="utf-8"))
    version = config.get("version")
    if not version:
        raise LoadError(f"No version in {BRANDS_FILE}")
    return str(version)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=BRANDED_DIR)
    parser.add_argument("--dry-run", action="store_true",
                        help="do everything, then roll back")
    args = parser.parse_args()

    try:
        entries = read_entries(args.input_dir)
        brands_version = _brands_version()
        engine = get_engine()

        with Session(engine) as session:
            known = set(session.scalars(select(Retailer.name)))
            validate_entries(entries, known)
            batch, warnings = build_batch(entries)
            stats = load_batch(session, batch, brands_version)
            if args.dry_run:
                session.rollback()
            else:
                session.commit()

            counts = {
                "listings": session.scalar(select(func.count()).select_from(Listing)),
                "listing_categories": session.scalar(
                    select(func.count()).select_from(ListingCategory)
                ),
                "price_history": session.scalar(
                    select(func.count()).select_from(PriceHistory)
                ),
            }
    except LoadError as error:
        raise SystemExit(f"Load failed, nothing written:\n{error}")

    mode = "DRY RUN (rolled back)" if args.dry_run else "LOADED"
    print(f"{mode}")
    print(f"  records read:          {len(entries)}")
    print(f"  unique (shop, url):    {len(batch)}")
    for key, value in stats.items():
        print(f"  {key + ':':<22} {value}")
    print(f"  duplicate warnings:    {len(warnings)}")
    for line in warnings[:20]:
        print(f"    {line}")
    print(f"Database now: {counts}")


if __name__ == "__main__":
    main()
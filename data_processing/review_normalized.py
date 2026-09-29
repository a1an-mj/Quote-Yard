"""
Quote Yard - Phase 2B review of normalized data.

Usage:
    python data_processing/review_normalized.py
    python data_processing/review_normalized.py --samples 5

Reads normalized_data/*.json and prints:
  1. Per product type: count per retailer + sample names
  2. Product types sold by only one retailer (no comparison possible)
  3. Spot-checks for the flagged mappings, with keyword hints
  4. parent_only / unmapped buckets with samples

Also writes reports/normalization_review.txt. Deterministic output.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = PROJECT_ROOT / "normalized_data"
REPORT_FILE = PROJECT_ROOT / "reports" / "normalization_review.txt"

# (shop, raw_category, raw_subcategory) -> keywords worth counting in names
FLAGGED = [
    ("Nandilath G Mart", "Kitchen Appliances", "Cooktop",
     ["hob", "gas stove", "cooktop", "induction"]),
    ("Pittappillil", "Kitchen Appliances", "Mixer Grinders",
     ["mixer", "grinder", "spice", "juicer"]),
    ("Pittappillil", "Kitchen Appliances", "Chimney & Hob",
     ["chimney", "hob", "cooktop", "hood"]),
    ("Pittappillil", "Kitchen Appliances", "Home Inverters & Batteries",
     ["inverter", "battery", "ups"]),
]


def load_records() -> list[dict]:
    records = []
    for path in sorted(NORMALIZED_DIR.glob("*.json")):
        records.extend(json.loads(path.read_text(encoding="utf-8")))
    return records


def pick_samples(names: list[str], n: int) -> list[str]:
    """Evenly spaced picks from the sorted unique names (deterministic)."""
    unique = sorted(set(names))
    if len(unique) <= n:
        return unique
    step = len(unique) / n
    return [unique[int(i * step)] for i in range(n)]


def build_report(records: list[dict], n_samples: int) -> list[str]:
    out: list[str] = []
    add = out.append

    # ---- 1. per product type -------------------------------------------
    by_type: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        if r["mapping_status"] == "mapped":
            by_type[(r["category"], r["product_type"])].append(r)

    add("=" * 78)
    add("1. PRODUCT TYPES (mapped records)")
    add("=" * 78)
    single_retailer = []
    for (category, ptype), items in sorted(by_type.items()):
        shops = Counter(r["shop"] for r in items)
        add(f"\n{category} > {ptype}  ({len(items)} records, {len(shops)} retailer(s))")
        for shop, count in sorted(shops.items()):
            add(f"    {shop:<20} {count}")
        for name in pick_samples([r["name"] for r in items], n_samples):
            add(f"      - {name[:90]}")
        if len(shops) == 1:
            single_retailer.append((category, ptype, next(iter(shops)), len(items)))

    # ---- 2. coverage ----------------------------------------------------
    add("\n" + "=" * 78)
    add("2. COMPARISON COVERAGE")
    add("=" * 78)
    multi = len(by_type) - len(single_retailer)
    add(f"\nProduct types with 2+ retailers: {multi} of {len(by_type)}")
    add("\nSingle-retailer types (no comparison possible yet):")
    for category, ptype, shop, count in single_retailer:
        add(f"    {category} > {ptype}: {shop} only ({count})")
    add("\nRetailers per type:")
    coverage = Counter(len({r['shop'] for r in items}) for items in by_type.values())
    for k in sorted(coverage):
        add(f"    {k} retailer(s): {coverage[k]} type(s)")

    # ---- 3. flagged spot-checks ------------------------------------------
    add("\n" + "=" * 78)
    add("3. FLAGGED MAPPINGS")
    add("=" * 78)
    for shop, cat, sub, keywords in FLAGGED:
        items = [
            r for r in records
            if r["shop"] == shop
            and r["raw_category"].casefold() == cat.casefold()
            and (r["raw_subcategory"] or "").casefold() == sub.casefold()
        ]
        add(f"\n{shop} / {cat} / {sub}  ({len(items)} records)")
        if not items:
            add("    NO RECORDS FOUND: check spelling in FLAGGED")
            continue
        add(f"    mapped to: {items[0]['category']} > {items[0]['product_type']}"
            f" ({items[0]['mapping_status']})")
        for kw in keywords:
            hits = sum(1 for r in items
                       if re.search(rf"\b{re.escape(kw)}", r["name"], re.I))
            add(f"    names containing '{kw}': {hits}")
        none = [r["name"] for r in items
                if not any(re.search(rf"\b{re.escape(k)}", r["name"], re.I)
                           for k in keywords)]
        add(f"    names matching NO keyword: {len(none)}")
        for name in pick_samples(none, 5):
            add(f"      ? {name[:90]}")
        for name in pick_samples([r["name"] for r in items], 8):
            add(f"      - {name[:90]}")

    # ---- 4. parent_only / unmapped ----------------------------------------
    add("\n" + "=" * 78)
    add("4. PARENT_ONLY AND UNMAPPED BUCKETS")
    add("=" * 78)
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        if r["mapping_status"] != "mapped":
            key = (r["mapping_status"], r["shop"], r["raw_category"],
                   r["raw_subcategory"])
            buckets[key].append(r)
    for (status, shop, cat, sub), items in sorted(
        buckets.items(), key=lambda kv: (kv[0][0], -len(kv[1]))
    ):
        add(f"\n[{status}] {shop} / {cat} / {sub}  ({len(items)} records)"
            f" -> category: {items[0]['category']}")
        for name in pick_samples([r["name"] for r in items], n_samples + 3):
            add(f"      - {name[:90]}")

    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=4)
    args = parser.parse_args()

    if not NORMALIZED_DIR.exists():
        raise FileNotFoundError(f"Run run_normalization.py first: {NORMALIZED_DIR}")

    records = load_records()
    lines = build_report(records, args.samples)
    text = "\n".join(lines) + "\n"

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(text, encoding="utf-8")
    print(text)
    print(f"Saved: {REPORT_FILE}")


if __name__ == "__main__":
    main()
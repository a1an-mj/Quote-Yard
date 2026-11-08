"""
Quote Yard - Phase 2B Normalization Runner

Usage:  python data_processing/run_normalization.py
Input:  cleaned_data/*.json
Output: normalized_data/*.json, reports/normalization_report.json

A product whose store category is not in aliases.json yet is skipped and listed
in the report, so one new store category doesn't hold back the day's prices.
If more than MAX_SKIPPED_SHARE of one store's products are skipped, that store
has probably renamed its categories: its files from the previous run are kept
instead (its listings then go stale, as when its scrape fails). Other stores
are not affected.
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from normalizer import (ALIASES_FILE, NAME_RULES_FILE, TAXONOMY_FILE, Normalizer,
                        load_json, normalize_file)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DATA_DIR = PROJECT_ROOT / "cleaned_data"
NORMALIZED_DATA_DIR = PROJECT_ROOT / "normalized_data"
TEMP_DIR = PROJECT_ROOT / "normalized_data.tmp"
REPORTS_DIR = PROJECT_ROOT / "reports"
NORMALIZATION_REPORT = REPORTS_DIR / "normalization_report.json"
MAX_SKIPPED_SHARE = 0.05


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def normalize_dir(normalizer: Normalizer, cleaned_dir: Path = CLEANED_DATA_DIR,
                  output_dir: Path = NORMALIZED_DATA_DIR, temp_dir: Path = TEMP_DIR,
                  report_path: Path = NORMALIZATION_REPORT) -> dict:
    json_files = sorted(cleaned_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files in {cleaned_dir}")

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    results = []  # (path, shop, records, normalized, errors)
    shop_in: Counter = Counter()
    shop_skipped: Counter = Counter()
    for input_path in json_files:
        records, normalized, errors = normalize_file(input_path, normalizer)
        shops = {r.get("shop") for r in records if r.get("shop")}
        shop = shops.pop() if len(shops) == 1 else None
        results.append((input_path, shop, records, normalized, errors))
        shop_in[shop] += len(records)
        shop_skipped[shop] += len(errors)

    held = sorted(
        s for s in shop_in
        if s is not None and shop_skipped[s] > MAX_SKIPPED_SHARE * shop_in[s]
    )
    # A file mixing stores, or without a store, can't be held back per store.
    held_none = shop_skipped[None] > 0

    files_report = []
    status_counts: Counter = Counter()
    typed_by_name = 0
    skipped_groups: dict[tuple, dict] = {}
    kept_previous = []
    total_in = total_ok = 0

    for input_path, shop, records, normalized, errors in results:
        if shop in held:
            previous = output_dir / input_path.name
            if previous.exists():
                shutil.copy2(previous, temp_dir / input_path.name)
                kept_previous.append(input_path.name)
            print(f"{input_path.name}: HELD BACK, {shop} has too many unknown categories")
        else:
            write_json(temp_dir / input_path.name, normalized)
            total_ok += len(normalized)
            status_counts.update(r["mapping_status"] for r in normalized)
            typed_by_name += sum(r["type_source"] == "name" for r in normalized)
            print(f"{input_path.name}: {len(normalized)}/{len(records)} normalized")
        total_in += len(records)

        for err in errors:
            group = skipped_groups.setdefault(
                (err["shop"], err["category"], err["subcategory"]),
                {"count": 0, "sample_product": err["name"], "error": err["error"]},
            )
            group["count"] += 1

        files_report.append({
            "file": input_path.name,
            "input_records": len(records),
            "normalized_records": len(normalized),
            "errors": len(errors),
            "held_back": shop in held,
        })

    unused = [" | ".join(k) for k in normalizer.unused_keys()]
    skipped = sum(shop_skipped.values())
    report = {
        "taxonomy_version": normalizer.version,
        "files_processed": len(json_files),
        "input_records": total_in,
        "normalized_records": total_ok,
        "errors": skipped,
        "skipped": skipped,
        "max_skipped_share": MAX_SKIPPED_SHARE,
        "held_back_shops": [
            {"shop": s, "skipped": shop_skipped[s], "products": shop_in[s]} for s in held
        ],
        "kept_previous_files": kept_previous,
        "mapping_status_counts": dict(status_counts),
        "typed_by_name": typed_by_name,
        "unmapped_combinations": [
            {"shop": k[0], "category": k[1], "subcategory": k[2], **v}
            for k, v in skipped_groups.items()
        ],
        "unused_alias_keys": unused,
        "files": files_report,
    }
    write_json(report_path, report)

    print(f"\nInput: {total_in}  Normalized: {total_ok}  Skipped: {skipped}")
    print(f"Status counts: {dict(status_counts)}  Typed by name: {typed_by_name}")
    for k, v in skipped_groups.items():
        print(f"SKIPPED {v['count']} in a new store category: {' / '.join(str(x) for x in k)}"
              f" (e.g. {v['sample_product']})")
    for s in held:
        print(f"HELD BACK {s}: {shop_skipped[s]} of {shop_in[s]} products in unknown "
              f"categories (over {MAX_SKIPPED_SHARE:.0%}); kept its previous data")
    if unused:
        print(f"WARNING: {len(unused)} unused alias key(s), see report")
    print(f"Report: {report_path}")

    if held_none:
        shutil.rmtree(temp_dir)  # keep the previous normalized_data untouched
        raise SystemExit("Normalization failed: unknown categories in a file without a "
                         "single store. Output not replaced.")

    if output_dir.exists():
        shutil.rmtree(output_dir)
    temp_dir.rename(output_dir)
    print(f"Output: {output_dir}")
    return report


def main() -> None:
    for path in (CLEANED_DATA_DIR, TAXONOMY_FILE, ALIASES_FILE, NAME_RULES_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Not found: {path}")
    normalizer = Normalizer(
        load_json(TAXONOMY_FILE), load_json(ALIASES_FILE), load_json(NAME_RULES_FILE)
    )
    normalize_dir(normalizer)


if __name__ == "__main__":
    main()

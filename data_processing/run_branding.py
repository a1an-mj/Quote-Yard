"""
Quote Yard - Phase 2C brand runner.

Usage:  python data_processing/run_branding.py
Input:  normalized_data/*.json
Output: branded_data/*.json, reports/brand_report.json
Unknown brands are reported, not errors.
"""

from __future__ import annotations

import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

from brand_extractor import BRANDS_FILE, BrandExtractor, fold, load_json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "normalized_data"
OUTPUT_DIR = PROJECT_ROOT / "branded_data"
TEMP_DIR = PROJECT_ROOT / "branded_data.tmp"
REPORT_FILE = PROJECT_ROOT / "reports" / "brand_report.json"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def main() -> None:
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Run run_normalization.py first: {INPUT_DIR}")

    extractor = BrandExtractor(load_json(BRANDS_FILE))
    files = sorted(INPUT_DIR.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files in {INPUT_DIR}")

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)

    total = matched = 0
    by_shop: dict[str, Counter] = defaultdict(Counter)
    brand_counts: Counter = Counter()
    unknown_tokens: Counter = Counter()
    unknown_samples: dict[str, list[str]] = defaultdict(list)
    unknown_by_shop: Counter = Counter()

    for path in files:
        records = json.loads(path.read_text(encoding="utf-8"))
        out = []
        for record in records:
            enriched = extractor.enrich(record)
            out.append(enriched)
            total += 1
            shop = record["shop"]
            by_shop[shop][enriched["brand_status"]] += 1
            if enriched["brand"]:
                matched += 1
                brand_counts[enriched["brand"]] += 1
            else:
                unknown_by_shop[shop] += 1
                words = fold(record["name"]).split()
                token = words[0] if words else "(empty)"
                unknown_tokens[token] += 1
                if len(unknown_samples[token]) < 3:
                    unknown_samples[token].append(record["name"][:80])
        write_json(TEMP_DIR / path.name, out)

    unknown = total - matched
    report = {
        "brands_version": extractor.version,
        "records": total,
        "matched": matched,
        "unknown": unknown,
        "match_rate": round(matched / total, 4),
        "by_shop": {s: dict(c) for s, c in sorted(by_shop.items())},
        "brand_counts": dict(brand_counts.most_common()),
        "unknown_leading_tokens": [
            {"token": t, "count": c, "samples": unknown_samples[t]}
            for t, c in unknown_tokens.most_common(60)
        ],
        "unused_brands": extractor.unused_brands(),
    }
    write_json(REPORT_FILE, report)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    TEMP_DIR.rename(OUTPUT_DIR)

    print(f"Records: {total}  Matched: {matched}  Unknown: {unknown} "
          f"({matched / total:.1%} matched)")
    for shop, counter in sorted(by_shop.items()):
        print(f"  {shop:<18} matched {counter['matched']:>4}  "
              f"unknown {counter['unknown']:>4}")
    print("\nTop unknown leading tokens:")
    for token, count in unknown_tokens.most_common(25):
        print(f"  {count:>4}  {token:<16} e.g. {unknown_samples[token][0]}")
    print(f"\nUnused brands in list: {len(extractor.unused_brands())}")
    print(f"Output: {OUTPUT_DIR}\nReport: {REPORT_FILE}")


if __name__ == "__main__":
    main()
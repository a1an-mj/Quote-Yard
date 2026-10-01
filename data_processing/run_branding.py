"""
Quote Yard - Phase 2C brand runner.

Usage:  python data_processing/run_branding.py
Input:  normalized_data/*.json
Output: branded_data/*.json, reports/brand_report.json
Unknown and review records are reported, not errors.
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

    total = 0
    status_counts: Counter = Counter()
    by_shop: dict[str, Counter] = defaultdict(Counter)
    brand_counts: Counter = Counter()
    unknown_tokens: Counter = Counter()
    unknown_samples: dict[str, list[str]] = defaultdict(list)
    review_groups: dict[tuple, dict] = {}

    for path in files:
        records = json.loads(path.read_text(encoding="utf-8"))
        out = []
        for record in records:
            enriched = extractor.enrich(record)
            out.append(enriched)
            total += 1
            status = enriched["brand_status"]
            status_counts[status] += 1
            by_shop[record["shop"]][status] += 1

            if status == "matched":
                brand_counts[enriched["brand"]] += 1
            elif status == "review":
                key = tuple(enriched["brand_candidates"])
                group = review_groups.setdefault(
                    key, {"count": 0, "samples": []}
                )
                group["count"] += 1
                if len(group["samples"]) < 3:
                    group["samples"].append(record["name"][:80])
            else:
                words = fold(record["name"]).split()
                token = words[0] if words else "(empty)"
                unknown_tokens[token] += 1
                if len(unknown_samples[token]) < 3:
                    unknown_samples[token].append(record["name"][:80])
        write_json(TEMP_DIR / path.name, out)

    matched = status_counts["matched"]
    report = {
        "brands_version": extractor.version,
        "records": total,
        "matched": matched,
        "review": status_counts["review"],
        "unknown": status_counts["unknown"],
        "match_rate": round(matched / total, 4),
        "by_shop": {s: dict(c) for s, c in sorted(by_shop.items())},
        "brand_counts": dict(brand_counts.most_common()),
        "review_groups": [
            {"candidates": list(k), **v}
            for k, v in sorted(review_groups.items(),
                               key=lambda kv: -kv[1]["count"])
        ],
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

    print(f"Records: {total}  Matched: {matched}  "
          f"Review: {status_counts['review']}  "
          f"Unknown: {status_counts['unknown']}  ({matched / total:.1%} matched)")
    for shop, c in sorted(by_shop.items()):
        print(f"  {shop:<18} matched {c['matched']:>4}  "
              f"review {c['review']:>3}  unknown {c['unknown']:>4}")
    if review_groups:
        print("\nReview groups (brand conflicts, brand left null):")
        for key, g in sorted(review_groups.items(), key=lambda kv: -kv[1]["count"]):
            print(f"  {g['count']:>3}  {' + '.join(key):<30} e.g. {g['samples'][0]}")
    print("\nTop unknown leading tokens:")
    for token, count in unknown_tokens.most_common(15):
        print(f"  {count:>4}  {token:<16} e.g. {unknown_samples[token][0]}")
    print(f"\nUnused brands in list: {len(extractor.unused_brands())}")
    print(f"Output: {OUTPUT_DIR}\nReport: {REPORT_FILE}")


if __name__ == "__main__":
    main()
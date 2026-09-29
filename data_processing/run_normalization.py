"""
Quote Yard - Phase 2B Normalization Runner

Usage:  python data_processing/run_normalization.py
Input:  cleaned_data/*.json
Output: normalized_data/*.json, reports/normalization_report.json
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from normalizer import ALIASES_FILE, TAXONOMY_FILE, Normalizer, load_json, normalize_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DATA_DIR = PROJECT_ROOT / "cleaned_data"
NORMALIZED_DATA_DIR = PROJECT_ROOT / "normalized_data"
TEMP_DIR = PROJECT_ROOT / "normalized_data.tmp"
REPORTS_DIR = PROJECT_ROOT / "reports"
NORMALIZATION_REPORT = REPORTS_DIR / "normalization_report.json"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def main() -> None:
    for path in (CLEANED_DATA_DIR, TAXONOMY_FILE, ALIASES_FILE):
        if not path.exists():
            raise FileNotFoundError(f"Not found: {path}")

    normalizer = Normalizer(load_json(TAXONOMY_FILE), load_json(ALIASES_FILE))

    json_files = sorted(CLEANED_DATA_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files in {CLEANED_DATA_DIR}")

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)

    files_report = []
    status_counts: Counter = Counter()
    error_groups: dict[tuple, dict] = {}
    total_in = total_ok = 0

    for input_path in json_files:
        records, normalized, errors = normalize_file(input_path, normalizer)
        write_json(TEMP_DIR / input_path.name, normalized)

        total_in += len(records)
        total_ok += len(normalized)
        status_counts.update(r["mapping_status"] for r in normalized)

        for err in errors:
            group = error_groups.setdefault(
                (err["shop"], err["category"], err["subcategory"]),
                {"count": 0, "sample_product": err["name"], "error": err["error"]},
            )
            group["count"] += 1

        files_report.append(
            {
                "file": input_path.name,
                "input_records": len(records),
                "normalized_records": len(normalized),
                "errors": len(errors),
            }
        )
        print(f"{input_path.name}: {len(normalized)}/{len(records)} normalized")

    total_errors = total_in - total_ok
    unused = [" | ".join(k) for k in normalizer.unused_keys()]

    report = {
        "taxonomy_version": normalizer.version,
        "files_processed": len(json_files),
        "input_records": total_in,
        "normalized_records": total_ok,
        "errors": total_errors,
        "mapping_status_counts": dict(status_counts),
        "unmapped_combinations": [
            {"shop": k[0], "category": k[1], "subcategory": k[2], **v}
            for k, v in error_groups.items()
        ],
        "unused_alias_keys": unused,
        "files": files_report,
    }
    write_json(NORMALIZATION_REPORT, report)

    print(f"\nInput: {total_in}  Normalized: {total_ok}  Errors: {total_errors}")
    print(f"Status counts: {dict(status_counts)}")
    if unused:
        print(f"WARNING: {len(unused)} unused alias key(s), see report")
    print(f"Report: {NORMALIZATION_REPORT}")

    if total_errors:
        shutil.rmtree(TEMP_DIR)  # keep the previous normalized_data untouched
        raise SystemExit(
            f"Normalization failed: {total_errors} record(s) in "
            f"{len(error_groups)} unmapped combination(s). Output not replaced."
        )

    if NORMALIZED_DATA_DIR.exists():
        shutil.rmtree(NORMALIZED_DATA_DIR)
    TEMP_DIR.rename(NORMALIZED_DATA_DIR)
    print(f"Output: {NORMALIZED_DATA_DIR}")


if __name__ == "__main__":
    main()
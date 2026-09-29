from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from .cleaner import clean_record
except ImportError:
    from cleaner import clean_record


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data"
CLEANED_DIR = PROJECT_ROOT / "cleaned_data"
REPORT_DIR = PROJECT_ROOT / "reports"


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path) -> list:
    """Load a JSON file and ensure its root is a list."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"{path.name}: JSON root must be a list"
        )

    return data


def save_json(path: Path, data) -> None:
    """Save data as formatted UTF-8 JSON."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# CLEAN ONE FILE
# ============================================================

def clean_file(
    input_path: Path,
    output_path: Path,
    seen: dict,
) -> dict:
    """
    Clean all records from one JSON file.

    Duplicate URLs are tracked but NOT removed.
    """

    records = load_json(input_path)

    cleaned_records = []

    errors = Counter()
    availability = Counter()

    for record in records:

        cleaned, record_errors = clean_record(record)

        # Record validation errors.
        for error in record_errors:
            errors[error] += 1

        # Skip invalid records.
        if cleaned is None:
            continue

        cleaned_records.append(cleaned)

        # Track availability.
        availability[
            cleaned["availability"]
        ] += 1

        # Track duplicate product URLs.
        #
        # Shop is included because the same URL on two
        # different retailers is not a duplicate listing.
        duplicate_key = (
            cleaned["shop"],
            cleaned["url"],
        )

        seen[duplicate_key].append(
            {
                "file": input_path.name,
                "name": cleaned["name"],
                "price": cleaned["price"],
                "category": cleaned["category"],
                "subcategory": cleaned["subcategory"],
            }
        )

    # Save cleaned version.
    save_json(
        output_path,
        cleaned_records,
    )

    return {
        "file": input_path.name,
        "input_records": len(records),
        "cleaned_records": len(cleaned_records),
        "removed_records": (
            len(records) - len(cleaned_records)
        ),
        "availability": dict(availability),
        "errors": dict(errors),
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    # Find all raw JSON files.
    json_files = sorted(
        RAW_DIR.glob("*.json")
    )

    if not json_files:
        print(
            "No JSON files found in data/"
        )
        return

    # Create output directories.
    CLEANED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Tracks:
    #
    # (shop, url) -> [
    #     {
    #         file,
    #         name,
    #         price,
    #         category,
    #         subcategory
    #     }
    # ]
    #
    # We use defaultdict(list) so multiple occurrences
    # can be stored without deleting anything.
    seen = defaultdict(list)

    file_results = []

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    print("=" * 70)
    print("QUOTE YARD - DATA CLEANING")
    print("=" * 70)

    # --------------------------------------------------------
    # PROCESS EACH FILE
    # --------------------------------------------------------

    for input_path in json_files:

        output_path = (
            CLEANED_DIR
            / input_path.name
        )

        result = clean_file(
            input_path,
            output_path,
            seen,
        )

        file_results.append(result)

        print(
            f"{result['file']:<40} "
            f"{result['input_records']:>5} → "
            f"{result['cleaned_records']:>5} "
            f"(removed: "
            f"{result['removed_records']})"
        )

    # --------------------------------------------------------
    # FIND DUPLICATE URL GROUPS
    # --------------------------------------------------------

    duplicates = []

    for (shop, url), locations in seen.items():

        if len(locations) > 1:

            duplicates.append(
                {
                    "shop": shop,
                    "url": url,
                    "occurrences": len(locations),
                    "locations": locations,
                }
            )

    # Sort duplicates for a stable report.
    duplicates.sort(
        key=lambda item: (
            item["shop"],
            item["url"],
        )
    )

    # --------------------------------------------------------
    # COMBINE AVAILABILITY COUNTS
    # --------------------------------------------------------

    total_availability = Counter()

    for result in file_results:

        total_availability.update(
            result["availability"]
        )

    # --------------------------------------------------------
    # COMBINE VALIDATION ERRORS
    # --------------------------------------------------------

    total_errors = Counter()

    for result in file_results:

        total_errors.update(
            result["errors"]
        )

    # --------------------------------------------------------
    # BUILD SUMMARY
    # --------------------------------------------------------

    summary = {
        "files_processed": len(
            file_results
        ),

        "input_records": sum(
            result["input_records"]
            for result in file_results
        ),

        "cleaned_records": sum(
            result["cleaned_records"]
            for result in file_results
        ),

        "removed_records": sum(
            result["removed_records"]
            for result in file_results
        ),

        "availability": dict(
            total_availability
        ),

        "validation_errors": dict(
            total_errors
        ),

        "duplicate_url_groups": len(
            duplicates
        ),

        "records_in_duplicate_groups": sum(
            duplicate["occurrences"]
            for duplicate in duplicates
        ),
    }

    # --------------------------------------------------------
    # BUILD COMPLETE REPORT
    # --------------------------------------------------------

    report = {
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "summary": summary,

        "files": file_results,

        "duplicates": duplicates,

        "cleaning_rules": [
            "Trim leading and trailing whitespace.",
            "Collapse consecutive whitespace.",
            "Clean product names conservatively.",
            "Require positive integer prices.",
            "Do not silently truncate fractional prices.",
            "Validate HTTP and HTTPS URLs.",
            "Convert missing availability to Unknown.",
            "Standardize obvious availability values.",
            "Preserve subcategory values.",
            "Do not normalize categories during cleaning.",
            "Do not normalize subcategories during cleaning.",
            "Do not remove duplicate URLs.",
            "Report duplicate URLs for later analysis.",
        ],
    }

    # --------------------------------------------------------
    # SAVE REPORT
    # --------------------------------------------------------

    report_path = (
        REPORT_DIR
        / "cleaning_report.json"
    )

    save_json(
        report_path,
        report,
    )

    # --------------------------------------------------------
    # FINAL TERMINAL REPORT
    # --------------------------------------------------------

    print("=" * 70)

    print(
        f"Files processed          : "
        f"{summary['files_processed']}"
    )

    print(
        f"Input records            : "
        f"{summary['input_records']}"
    )

    print(
        f"Cleaned records          : "
        f"{summary['cleaned_records']}"
    )

    print(
        f"Removed records          : "
        f"{summary['removed_records']}"
    )

    print(
        f"Duplicate URL groups     : "
        f"{summary['duplicate_url_groups']}"
    )

    print(
        f"Records in duplicate groups: "
        f"{summary['records_in_duplicate_groups']}"
    )

    print("\nAvailability:")

    for status, count in (
        total_availability.most_common()
    ):
        print(
            f"  {status:<20}: {count}"
        )

    if total_errors:

        print("\nValidation errors:")

        for error, count in (
            total_errors.items()
        ):
            print(
                f"  {error:<35}: "
                f"{count}"
            )

    else:

        print(
            "\nNo validation errors found."
        )

    print(
        f"\nReport written to:"
        f"\n{report_path}"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
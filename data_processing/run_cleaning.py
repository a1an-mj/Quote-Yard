from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from cleaner import clean_record


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data"
CLEANED_DIR = PROJECT_ROOT / "cleaned_data"


def load_json(path: Path) -> list:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("JSON root must be a list")

    return data


def save_json(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def clean_file(input_path: Path, output_path: Path) -> dict:
    records = load_json(input_path)

    cleaned_records = []

    error_counter = Counter()

    for record in records:
        cleaned, errors = clean_record(record)

        if cleaned is not None:
            cleaned_records.append(cleaned)

        for error in errors:
            error_counter[error] += 1

    save_json(output_path, cleaned_records)

    return {
        "file": input_path.name,
        "input_records": len(records),
        "cleaned_records": len(cleaned_records),
        "removed_records": len(records) - len(cleaned_records),
        "errors": dict(error_counter),
    }


def main() -> None:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(RAW_DIR.glob("*.json"))

    if not json_files:
        print("No JSON files found in data/")
        return

    total_input = 0
    total_cleaned = 0
    total_removed = 0

    all_errors = Counter()

    print("=" * 70)
    print("QUOTE YARD - DATA CLEANING")
    print("=" * 70)

    for input_path in json_files:
        output_path = CLEANED_DIR / input_path.name

        result = clean_file(input_path, output_path)

        total_input += result["input_records"]
        total_cleaned += result["cleaned_records"]
        total_removed += result["removed_records"]

        all_errors.update(result["errors"])

        print(
            f"{result['file']:<40} "
            f"{result['input_records']:>5} → "
            f"{result['cleaned_records']:>5} "
            f"(removed: {result['removed_records']})"
        )

    print("=" * 70)
    print(f"Files processed : {len(json_files)}")
    print(f"Input records   : {total_input}")
    print(f"Cleaned records : {total_cleaned}")
    print(f"Removed records : {total_removed}")

    if all_errors:
        print("\nValidation issues:")
        for error, count in all_errors.items():
            print(f"  {error}: {count}")
    else:
        print("\nNo validation errors found.")

    print("=" * 70)


if __name__ == "__main__":
    main()
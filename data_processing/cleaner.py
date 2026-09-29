from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REQUIRED_FIELDS = {
    "name",
    "price",
    "url",
    "availability",
    "shop",
    "category",
}

OPTIONAL_FIELDS = {
    "subcategory",
}


def clean_string(value: Any) -> str | None:
    """Clean basic whitespace without changing product meaning."""
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    # Replace unusual whitespace with normal spaces
    value = re.sub(r"\s+", " ", value)

    # Remove leading/trailing whitespace
    value = value.strip()

    return value or None


def clean_name(value: Any) -> str | None:
    """Clean product name conservatively."""
    return clean_string(value)


def clean_price(value: Any) -> int | None:
    """
    Convert price into a positive integer.

    Examples:
        42999 -> 42999
        "₹42,999" -> 42999
        "₹42,999.00" -> 42999
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        price = int(value)
        return price if price > 0 else None

    value = str(value).strip()

    if not value:
        return None

    # Remove currency symbols, commas and spaces.
    cleaned = re.sub(r"[₹,\s]", "", value)

    # Handle decimal prices such as 42999.00
    try:
        price = float(cleaned)
    except ValueError:
        return None

    price = int(price)

    return price if price > 0 else None


def clean_url(value: Any) -> str | None:
    """Validate and lightly clean a product URL."""
    value = clean_string(value)

    if not value:
        return None

    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"}:
        return None

    if not parsed.netloc:
        return None

    return value


def clean_availability(value: Any) -> str:
    """
    Standardize availability without guessing.

    Missing/unknown availability becomes 'Unknown'.
    We deliberately do NOT convert missing values to 'Out of stock'.
    """
    value = clean_string(value)

    if not value:
        return "Unknown"

    normalized = value.lower()

    if normalized in {
        "in stock",
        "instock",
        "available",
        "available now",
    }:
        return "In stock"

    if normalized in {
        "out of stock",
        "outofstock",
        "unavailable",
    }:
        return "Out of stock"

    # Preserve unusual values rather than guessing.
    return value


def clean_record(record: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """
    Clean one product record.

    Returns:
        (cleaned_record, errors)
    """
    errors: list[str] = []

    if not isinstance(record, dict):
        return None, ["record_is_not_an_object"]

    # Check required fields.
    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if field not in record
    ]

    if missing_fields:
        errors.extend(
            f"missing_required_field:{field}"
            for field in missing_fields
        )

    # Clean fields.
    name = clean_name(record.get("name"))
    price = clean_price(record.get("price"))
    url = clean_url(record.get("url"))
    availability = clean_availability(record.get("availability"))
    shop = clean_string(record.get("shop"))
    category = clean_string(record.get("category"))
    subcategory = clean_string(record.get("subcategory"))

    # Validate cleaned values.
    if not name:
        errors.append("invalid_name")

    if price is None:
        errors.append("invalid_price")

    if not url:
        errors.append("invalid_url")

    if not shop:
        errors.append("invalid_shop")

    if not category:
        errors.append("invalid_category")

    # Don't keep invalid records.
    if errors:
        return None, errors

    cleaned = {
        "name": name,
        "price": price,
        "url": url,
        "availability": availability,
        "shop": shop,
        "category": category,
        "subcategory": subcategory,
    }

    return cleaned, []
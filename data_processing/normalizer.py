"""
Quote Yard - Phase 2B Normalizer

Applies the canonical taxonomy (taxonomy.json) using explicit
retailer/category/subcategory mappings (aliases.json).

Rules:
- Never modify raw or cleaned data.
- Never guess a product type.
- Preserve raw category/subcategory values.
- Fail on unknown mapping combinations.
- Deterministic and idempotent: reads raw_* fields when present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
TAXONOMY_DIR = BASE_DIR / "taxonomy"
TAXONOMY_FILE = TAXONOMY_DIR / "taxonomy.json"
ALIASES_FILE = TAXONOMY_DIR / "aliases.json"

NONE_KEY = "__none__"
VALID_STATUSES = {"mapped", "parent_only", "unmapped"}


class MappingError(ValueError):
    """A record or mapping file could not be normalized."""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def fold(value: Any) -> str:
    """Casefold a lookup value; None or blank becomes the null sentinel."""
    if value is None:
        return NONE_KEY
    text = " ".join(str(value).split()).casefold()
    return text or NONE_KEY


class Normalizer:
    def __init__(self, taxonomy: dict, aliases: dict) -> None:
        # Guardrail 4: both files must be versioned together.
        taxonomy_version = taxonomy.get("version")
        aliases_version = aliases.get("taxonomy_version")
        if taxonomy_version != aliases_version:
            raise MappingError(
                f"Version mismatch: taxonomy.json version="
                f"{taxonomy_version!r}, aliases.json taxonomy_version="
                f"{aliases_version!r}"
            )
        self.version = taxonomy_version

        # product type -> parent category (types must be globally unique)
        self.type_to_parent: dict[str, str] = {}
        for parent, types in taxonomy["categories"].items():
            for product_type in types:
                if product_type in self.type_to_parent:
                    raise MappingError(
                        f"Duplicate product type in taxonomy: {product_type}"
                    )
                self.type_to_parent[product_type] = parent
        self.parents = set(taxonomy["categories"])

        # (shop, category, subcategory), all casefolded -> mapping
        self.index: dict[tuple[str, str, str], dict] = {}
        for shop, categories in aliases["mappings"].items():
            for category, subcategories in categories.items():
                for subcategory, mapping in subcategories.items():
                    key = (fold(shop), fold(category), fold(subcategory))
                    if key in self.index:
                        raise MappingError(
                            f"Two aliases collapse to the same key: {key}"
                        )
                    self._check_mapping(key, mapping)
                    self.index[key] = mapping

        self.used_keys: set[tuple[str, str, str]] = set()

    def _check_mapping(self, key: tuple, mapping: dict) -> None:
        status = mapping.get("status")
        product_type = mapping.get("product_type")

        if status not in VALID_STATUSES:
            raise MappingError(f"Invalid status {status!r} for {key}")

        if status == "mapped":
            if product_type not in self.type_to_parent:
                raise MappingError(
                    f"{key}: product type {product_type!r} not in taxonomy"
                )
        else:
            if product_type is not None:
                raise MappingError(
                    f"{key}: status {status!r} must have product_type null"
                )
            if status == "parent_only" and mapping.get("category") not in self.parents:
                raise MappingError(
                    f"{key}: parent_only category "
                    f"{mapping.get('category')!r} not in taxonomy"
                )

    def normalize_product(self, product: dict) -> dict:
        """Return a new normalized dict; the input is never modified."""
        shop = product.get("shop")
        if not shop:
            raise MappingError("Product is missing 'shop'.")

        # Idempotency: prefer raw_* fields if already normalized.
        raw_category = (
            product["raw_category"] if "raw_category" in product
            else product.get("category")
        )
        raw_subcategory = (
            product["raw_subcategory"] if "raw_subcategory" in product
            else product.get("subcategory")
        )
        if not raw_category:
            raise MappingError(f"Product missing category: {product.get('name')}")

        key = (fold(shop), fold(raw_category), fold(raw_subcategory))
        mapping = self.index.get(key)
        if mapping is None:
            raise MappingError(
                f"Unknown mapping: {shop} / {raw_category} / {raw_subcategory}"
            )
        self.used_keys.add(key)

        status = mapping["status"]
        product_type = mapping["product_type"]
        if status == "mapped":
            category = self.type_to_parent[product_type]
        elif status == "parent_only":
            category = mapping["category"]
        else:
            category = None

        normalized = dict(product)
        normalized["raw_category"] = raw_category
        normalized["raw_subcategory"] = raw_subcategory
        normalized["category"] = category
        normalized["product_type"] = product_type
        normalized["mapping_status"] = status
        normalized["taxonomy_version"] = self.version
        return normalized

    def unused_keys(self) -> list[tuple[str, str, str]]:
        return sorted(set(self.index) - self.used_keys)


def normalize_records(
    records: list[dict], normalizer: Normalizer
) -> tuple[list[dict], list[dict]]:
    normalized: list[dict] = []
    errors: list[dict] = []
    for index, product in enumerate(records):
        try:
            normalized.append(normalizer.normalize_product(product))
        except MappingError as error:
            errors.append(
                {
                    "index": index,
                    "name": product.get("name"),
                    "shop": product.get("shop"),
                    "category": product.get("raw_category", product.get("category")),
                    "subcategory": product.get(
                        "raw_subcategory", product.get("subcategory")
                    ),
                    "error": str(error),
                }
            )
    return normalized, errors


def normalize_file(input_path: Path, normalizer: Normalizer):
    """Read one file and return (normalized_records, errors). Writes nothing."""
    records = load_json(input_path)
    if not isinstance(records, list):
        raise MappingError(f"Expected a list of products in {input_path}")
    normalized, errors = normalize_records(records, normalizer)
    return records, normalized, errors
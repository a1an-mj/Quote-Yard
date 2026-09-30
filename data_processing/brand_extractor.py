"""
Quote Yard - Phase 2C brand extraction.

Explicit brand list only (brands.json). Never guesses: no match means
brand = None, brand_status = "unknown".

Matching: casefold, strip punctuation, whole-token search. The earliest
match in the name wins; the longest alias wins ties. Brands listed in
"start_only" match only at the start of the name (e.g. "HP" vs "1.5 HP").
Reads only `name`, so it is deterministic and idempotent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
BRANDS_FILE = BASE_DIR / "brands.json"


class BrandError(ValueError):
    """The brand file is invalid."""


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def fold(text: Any) -> str:
    """Casefold, replace punctuation with spaces, collapse whitespace."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(text).casefold()).split())


class BrandExtractor:
    def __init__(self, config: dict) -> None:
        self.version = config.get("version")
        brands: dict[str, list[str]] = config["brands"]
        start_only = set(config.get("start_only", []))

        missing = start_only - set(brands)
        if missing:
            raise BrandError(f"start_only brands not in list: {sorted(missing)}")

        self.aliases: list[tuple[str, str, bool]] = []
        seen: dict[str, str] = {}
        for brand, extra in brands.items():
            for alias in [brand, *extra]:
                key = fold(alias)
                if not key:
                    raise BrandError(f"Empty alias for {brand}")
                if key in seen and seen[key] != brand:
                    raise BrandError(
                        f"Alias {key!r} used by both {seen[key]} and {brand}"
                    )
                if key in seen:
                    continue  # same brand repeating its own name
                seen[key] = brand
                self.aliases.append((key, brand, brand in start_only))

        self.brand_names = set(brands)
        self.used: set[str] = set()

    def extract(self, name: str) -> str | None:
        text = f" {fold(name)} "
        best: tuple[int, int] | None = None
        best_brand: str | None = None
        for alias, brand, start_only in self.aliases:
            pos = text.find(f" {alias} ")
            if pos == -1 or (start_only and pos != 0):
                continue
            rank = (pos, -len(alias))
            if best is None or rank < best:
                best, best_brand = rank, brand
        if best_brand:
            self.used.add(best_brand)
        return best_brand

    def enrich(self, product: dict) -> dict:
        """Return a new dict with brand and brand_status added."""
        brand = self.extract(product.get("name", ""))
        result = dict(product)
        result["brand"] = brand
        result["brand_status"] = "matched" if brand else "unknown"
        return result

    def unused_brands(self) -> list[str]:
        return sorted(self.brand_names - self.used)
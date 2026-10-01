"""
Quote Yard - Phase 2C brand extraction.

Explicit brand list only (brands.json). Never guesses.

Matching: casefold, strip punctuation, whole-token search. Brands listed
in "start_only" match only at the start of the name (e.g. "HP" vs "1.5 HP").
A match fully inside a longer match is dropped ("Prestige" inside
"TTK Prestige").

Outcome per name:
  no brand found        -> brand None,  status "unknown"
  exactly one brand     -> brand set,   status "matched"
  two or more brands    -> brand None,  status "review",
                           brand_candidates = brands in name order
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

    def _matches(self, name: str) -> list[tuple[int, int, str]]:
        """All kept matches as (start, end, brand), ordered by position."""
        text = f" {fold(name)} "
        found = []
        for alias, brand, start_only in self.aliases:
            pos = text.find(f" {alias} ")
            if pos == -1 or (start_only and pos != 0):
                continue
            found.append((pos + 1, pos + 1 + len(alias), brand))

        def inside_longer(m):
            return any(
                o is not m
                and o[0] <= m[0]
                and m[1] <= o[1]
                and (o[1] - o[0]) > (m[1] - m[0])
                for o in found
            )

        return sorted(m for m in found if not inside_longer(m))

    def classify(self, name: str) -> tuple[str | None, str, list[str]]:
        """Return (brand, status, candidates)."""
        candidates: list[str] = []
        for _, _, brand in self._matches(name):
            if brand not in candidates:
                candidates.append(brand)

        self.used.update(candidates)

        if not candidates:
            return None, "unknown", []
        if len(candidates) == 1:
            return candidates[0], "matched", candidates
        return None, "review", candidates

    def extract(self, name: str) -> str | None:
        """The brand when exactly one is found, else None."""
        return self.classify(name)[0]

    def enrich(self, product: dict) -> dict:
        """Return a new dict with brand, brand_status, brand_candidates."""
        brand, status, candidates = self.classify(product.get("name", ""))
        result = dict(product)
        result["brand"] = brand
        result["brand_status"] = status
        result["brand_candidates"] = candidates if status == "review" else None
        return result

    def unused_brands(self) -> list[str]:
        return sorted(self.brand_names - self.used)
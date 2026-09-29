import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data_processing"))

from normalizer import (ALIASES_FILE, TAXONOMY_FILE, MappingError,
                        Normalizer, load_json)


@pytest.fixture(scope="module")
def norm():
    return Normalizer(load_json(TAXONOMY_FILE), load_json(ALIASES_FILE))


def product(shop, cat, sub=None):
    return {"name": "x", "price": 1, "url": "https://x", "availability": "In stock",
            "shop": shop, "category": cat, "subcategory": sub}


def test_mapped_and_parent_lookup(norm):
    r = norm.normalize_product(product("Nandilath G Mart", "Home Audio", "Sound Bars"))
    assert (r["category"], r["product_type"], r["mapping_status"]) == \
        ("Home Audio", "Soundbar", "mapped")


def test_null_subcategory_and_casefold(norm):
    r = norm.normalize_product(product("myG", "Mobiles"))
    assert r["product_type"] == "Mobile Phone"
    r = norm.normalize_product(product("Nandilath G Mart", "Kitchen Appliances", "Gas Stove"))
    assert r["product_type"] == "Gas Stove"      # alias key is "Gas stove"


def test_parent_only_and_unmapped(norm):
    r = norm.normalize_product(product("myG", "Personal Care"))
    assert (r["category"], r["product_type"]) == ("Personal Care", None)
    r = norm.normalize_product(product("myG", "Home & Kitchen"))
    assert r["category"] is None and r["mapping_status"] == "unmapped"


def test_unknown_combination_fails(norm):
    with pytest.raises(MappingError):
        norm.normalize_product(product("myG", "Brand New Category"))


def test_input_not_mutated_and_idempotent(norm):
    p = product("Pittappillil", "Home Appliances", "Split AC")
    before = copy.deepcopy(p)
    once = norm.normalize_product(p)
    assert p == before
    assert norm.normalize_product(once) == once


def test_version_mismatch_fails():
    tax, ali = load_json(TAXONOMY_FILE), load_json(ALIASES_FILE)
    ali["taxonomy_version"] = "9.9"
    with pytest.raises(MappingError):
        Normalizer(tax, ali)


def test_every_observed_tuple_is_mapped(norm):
    cleaned = ROOT / "cleaned_data"
    if not cleaned.exists():
        pytest.skip("cleaned_data/ not present")
    for path in cleaned.glob("*.json"):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            norm.normalize_product(rec)
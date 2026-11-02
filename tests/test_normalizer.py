import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data_processing"))

from normalizer import (ALIASES_FILE, NAME_RULES_FILE, TAXONOMY_FILE, MappingError,
                        Normalizer, load_json)


@pytest.fixture(scope="module")
def norm():
    return Normalizer(load_json(TAXONOMY_FILE), load_json(ALIASES_FILE), load_json(NAME_RULES_FILE))


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
        Normalizer(tax, ali, load_json(NAME_RULES_FILE))


def test_name_rules_version_mismatch_fails():
    rules = load_json(NAME_RULES_FILE)
    rules["taxonomy_version"] = "9.9"
    with pytest.raises(MappingError):
        Normalizer(load_json(TAXONOMY_FILE), load_json(ALIASES_FILE), rules)


def test_name_rule_type_must_be_in_taxonomy():
    rules = load_json(NAME_RULES_FILE)
    rules["rules"].append({"product_type": "Flying Car", "pattern": "car"})
    with pytest.raises(MappingError):
        Normalizer(load_json(TAXONOMY_FILE), load_json(ALIASES_FILE), rules)


def named(norm, name, shop="myG", cat="Home & Kitchen", sub=None):
    return norm.normalize_product({**product(shop, cat, sub), "name": name})


def test_name_gives_the_type_when_the_category_does_not(norm):
    r = named(norm, "Philips Dry Iron | 1000 W | HD1182/28")
    assert (r["category"], r["product_type"], r["mapping_status"], r["type_source"]) == \
        ("Home Appliances", "Iron", "mapped", "name")


def test_store_category_beats_the_name(norm):
    r = named(norm, "Philips Dry Iron", "Nandilath G Mart", "Home Audio", "Sound Bars")
    assert (r["product_type"], r["type_source"]) == ("Soundbar", "category")


@pytest.mark.parametrize("name, expected", [
    ("Lenovo LOQ Gaming Laptop | AMD Ryzen 7 | 16GB | 512 GB SSD", "Laptop"),
    ("Luker Turbine BLDC Ceiling Fan With Remote | 1200mm", "Ceiling Fan"),
    ("Philips Beard Trimmer for Men | Grey", "Trimmer & Shaver"),
    ("INVERTER BATTERY V-GUARD VT 12V-200 (200AH)", "Battery"),
    ("INVERTER V-GUARD PRIME 1650", "Inverter"),
    ("Godrej 1 Ton 3 Star Convertible Smart Inverter AC", "Air Conditioner"),
    ("Nolta Cast Iron Fry Pan | 24cm", "Cookware"),
    ("Milton Pro Cook Granito Non Induction Fry Pan | 16 Cm", "Cookware"),
    ("HP 886C 64GB OTG 3.2 Flash Drive", "Flash Drive"),
    ("Preethi Zodiac X Juicer Mixer Grinder | 750 W", "Mixer Grinder"),
    ("boAt CineHead E1 Smart Projector | 1080p & 4K Support", "Projector"),
])
def test_name_rule_picks_the_right_type(norm, name, expected):
    assert named(norm, name)["product_type"] == expected


@pytest.mark.parametrize("name", [
    "Apple USB-C to Lightning Cable | 1 Meter",
    "i Gear Core mini Compact charger Adapter | 20W",
    "HP USB C 5 in 1 Hub",
    "Fujifilm Instax Colorfilm Glosy | 10 Sheets",
    "Laptop Sleeve 15 inch",
    "Refrigerator Cover | Multicolor",
    "PUREFLAMES 3B GOLD",
])
def test_parts_and_vague_names_get_no_type(norm, name):
    r = named(norm, name)
    assert r["product_type"] is None and r["mapping_status"] == "unmapped"


def test_every_observed_tuple_is_mapped(norm):
    cleaned = ROOT / "cleaned_data"
    if not cleaned.exists():
        pytest.skip("cleaned_data/ not present")
    for path in cleaned.glob("*.json"):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            norm.normalize_product(rec)
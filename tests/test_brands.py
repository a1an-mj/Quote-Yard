import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data_processing"))

from brand_extractor import BRANDS_FILE, BrandError, BrandExtractor, load_json


@pytest.fixture(scope="module")
def ex():
    return BrandExtractor(load_json(BRANDS_FILE))


def test_simple_and_case(ex):
    assert ex.extract("Samsung Galaxy A07 5G (Black, 128 GB)") == "Samsung"
    assert ex.extract("realme 16 Pro+ 5G | 12 GB | 256 GB") == "realme"
    assert ex.extract("SAMSUNG GALAXY S25 5G 256 GB") == "Samsung"


def test_brand_not_first_word(ex):
    assert ex.extract("MIXER GRINDER PANASONIC MX-GC3550 WHITE") == "Panasonic"
    assert ex.extract("INVERTER BATTERY V-GUARD VJ 12V-145") == "V-Guard"
    assert ex.extract("Solarium Neo Instant Crompton Water Heater") == "Solarium"


def test_aliases_and_longest(ex):
    assert ex.extract("V Guard Cook Top 3 Burner") == "V-Guard"
    assert ex.extract("TTK Prestige Cooker") == "TTK Prestige"


def test_start_only(ex):
    assert ex.extract("Voltas 1.5 HP Split AC") == "Voltas"
    assert ex.extract("AC Cassette 1.5 HP") is None
    assert ex.extract("HP Pavilion 15 Laptop") == "HP"


def test_unknown_is_none(ex):
    r = ex.enrich({"name": "Zorblax Turbo Mixer", "shop": "x"})
    assert r["brand"] is None and r["brand_status"] == "unknown"


def test_enrich_pure_and_idempotent(ex):
    p = {"name": "LG 260 L Refrigerator", "shop": "x"}
    once = ex.enrich(p)
    assert "brand" not in p
    assert ex.enrich(once) == once


def test_duplicate_alias_rejected():
    with pytest.raises(BrandError):
        BrandExtractor({"version": "1", "brands": {"A": ["x"], "B": ["x"]}})
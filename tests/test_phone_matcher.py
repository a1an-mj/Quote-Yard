import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from matching.phone_matcher import match, parse_listing


def rec(name, shop="Oxygen", brand=None, price=10000, status="matched", url=None):
    return {"name": name, "shop": shop, "brand": brand, "brand_status": status,
            "price": price, "url": url or f"https://x/{shop}/{name}"}


def keys(groups):
    return {g["match_key"]: sorted(m["shop"] for m in g["listings"]) for g in groups}


def test_same_phone_four_formats_one_group():
    groups, review, skipped = match([
        rec("REDMI A7 (Sky Blue, 64 GB) (3 GB RAM)", "Oxygen", "Xiaomi"),
        rec("Redmi A7 (3GB RAM/64GB Storage, Black)", "Nandilath G Mart", "Xiaomi"),
        rec("Redmi A7 | 3 GB | 64 GB | Black", "myG", "Xiaomi"),
        rec("XIAOMI REDMI A7 (3+64GB) BLACK MOBILE PHONE", "Pittappillil", "Xiaomi"),
    ])
    assert keys(groups) == {"xiaomi|redmia7||3|64|": ["Nandilath G Mart", "Oxygen", "Pittappillil", "myG"]}
    assert not review and not skipped


def test_variant_words_keep_models_apart():
    groups, _, _ = match([
        rec("Samsung Galaxy S26 5G (White, 256 GB) (12 GB RAM)", "Oxygen", "Samsung"),
        rec("Samsung Galaxy S26 Ultra 5G | 12GB | 256GB | White", "myG", "Samsung"),
        rec("Redmi Note 17 5G | 8 GB | 128 GB | Dark Night", "myG", "Xiaomi"),
        rec("Redmi Note 17 Pro 5G (8GB RAM/128GB Storage, Blue)", "Nandilath G Mart", "Xiaomi"),
        rec("realme 16 5G (Air Black, 256 GB) (8 GB RAM)", "Oxygen", "realme"),
        rec("Realme 16 Pro+ 5G (8GB/256GB, Black)", "Nandilath G Mart", "realme"),
    ])
    assert len(groups) == 6
    assert all(len(g["shops"]) == 1 for g in groups)


def test_ram_and_storage_must_agree_colour_ignored():
    groups, _, _ = match([
        rec("Samsung Galaxy A07 5G (Black, 128 GB) (4 GB RAM)", "Oxygen", "Samsung"),
        rec("Samsung Galaxy A07 5G (Light Green, 128 GB) (6 GB RAM)", "Oxygen", "Samsung"),
        rec("Samsung A07 5G (4GB/128GB Storage, Light Violet)", "Nandilath G Mart", "Samsung"),
    ])
    assert keys(groups) == {"samsung|a07|5g|4|128|": ["Nandilath G Mart", "Oxygen"],
                            "samsung|a07|5g|6|128|": ["Oxygen"]}


def test_galaxy_optional_and_spacing_ignored():
    a = parse_listing(rec("Samsung A17 5G (6GB/128GB Storage, Black)", brand="Samsung"))
    b = parse_listing(rec("SAMSUNG GALAXY A17 5G 6GB RAM, 128GB STORAGE GRAY", brand="Samsung"))
    assert a["model_key"] == b["model_key"] == "a17"
    c = parse_listing(rec("Vivo V70FE (Purple, 256 GB) (8 GB RAM)", brand="Vivo"))
    d = parse_listing(rec("vivo V70 FE (Purple 2026, 256 GB) (8 GB RAM)", brand="Vivo"))
    assert c["model_key"] == d["model_key"] == "v70fe"


def test_nothing_parenthesised_model():
    r = parse_listing(rec("Nothing Phone (4a) Pro (Silver, 128 GB) (8 GB RAM)", brand="Nothing"))
    assert r["model"] == "4a pro" and r["skip_reason"] is None
    assert parse_listing(rec("Nothing Phone 4a Pro | 12 GB | 256 GB", brand="Nothing"))["model_key"] == "4apro"


def test_lte_is_4g_and_separate_from_5g():
    groups, review, _ = match([
        rec("Samsung Galaxy A07 LTE (Black, 64 GB) (4 GB RAM)", "Oxygen", "Samsung"),
        rec("Samsung A07 5G (4GB/64GB Storage, Black)", "Nandilath G Mart", "Samsung"),
    ])
    assert set(keys(groups)) == {"samsung|a07|4g|4|64|", "samsung|a07|5g|4|64|"}
    assert review[0]["reason"] == "network_differs"


def test_missing_network_joins_single_known_network():
    groups, review, _ = match([
        rec("Redmi A7 Pro (4GB RAM/64GB Storage, Black)", "Nandilath G Mart", "Xiaomi"),
        rec("REDMI A7 Pro 5G (Black, 64 GB) (4 GB RAM)", "Oxygen", "Xiaomi"),
    ])
    assert keys(groups) == {"xiaomi|redmia7pro|5g|4|64|": ["Nandilath G Mart", "Oxygen"]}
    assert not review


def test_missing_network_ambiguous_goes_to_review():
    groups, review, _ = match([
        rec("Samsung Galaxy A07 LTE (Black, 64 GB) (4 GB RAM)", "Oxygen", "Samsung"),
        rec("Samsung Galaxy A07 5G (Black, 128 GB) (4 GB RAM)", "Oxygen", "Samsung"),
        rec("Samsung A07 (4GB/64GB Storage, Black)", "Nandilath G Mart", "Samsung"),
    ])
    assert [r["reason"] for r in review] == ["network_ambiguous"]
    assert review[0]["listings"][0]["shop"] == "Nandilath G Mart"
    assert sum(len(g["listings"]) for g in groups) == 2


def test_bundle_is_part_of_the_key():
    groups, review, _ = match([
        rec("vivo X300 Ultra (Eclipse Black - Photographer Kit, 512 GB) (16 GB RAM)", "Oxygen", "Vivo"),
        rec("Vivo X300 Ultra With Photographer Kit | 16 GB | 512 GB | Eclipse Black", "myG", "Vivo"),
        rec("Vivo X300 Ultra (16GB/512GB Storage, Eclipse Black)", "Nandilath G Mart", "Vivo"),
    ])
    k = keys(groups)
    assert k["vivo|x300ultra||16|512|photographer kit"] == ["Oxygen", "myG"]
    assert k["vivo|x300ultra||16|512|"] == ["Nandilath G Mart"]
    assert [r["reason"] for r in review] == ["package_differs"]


def test_box_note_merges_and_is_tracked():
    groups, review, _ = match([
        rec("Samsung Galaxy A17 5G Without Adapter (Black, 128 GB) (6 GB RAM)", "Oxygen", "Samsung"),
        rec("Samsung A17 5G (6GB/128GB Storage, Black)", "Nandilath G Mart", "Samsung"),
    ])
    assert keys(groups) == {"samsung|a17|5g|6|128|": ["Nandilath G Mart", "Oxygen"]}
    g = groups[0]
    assert g["box_notes"] == ["without adapter"]
    assert {m["shop"]: m["box_note"] for m in g["listings"]} == {
        "Oxygen": "without adapter", "Nandilath G Mart": None}
    assert "Adapter" not in g["name"]
    assert not review


def test_pittappillil_smart_dropped_after_brand_only():
    a = parse_listing(rec("NOTHING SMART 4B 5G (8+256GB) WHITE", "Pittappillil", "Nothing"))
    b = parse_listing(rec("Nothing Phone (4b) (Black, 256 GB) (8 GB RAM)", "Oxygen", "Nothing"))
    assert a["model_key"] == b["model_key"] == "4b"
    m = parse_listing(rec("MOTOROLA SMART G06 POWER 4G (4+64GB) TENDRIL", "Pittappillil", "Motorola"))
    assert m["model"] == "g06 power"
    # other shops keep the word, and it is only dropped straight after the brand
    assert parse_listing(rec("Nothing Smart 4B 5G (8+256GB)", "Oxygen", "Nothing"))["model"] == "smart 4b"
    assert parse_listing(rec("BOAT WAVE SMART 3 (2+16GB)", "Pittappillil", "boAt"))["model"] == "wave smart 3"


def test_apple_ram_ignored():
    groups, _, skipped = match([
        rec("Apple iPhone 17 | 256 GB | Black | NM", "myG", "Apple"),
        rec("Apple iPhone 17 ( 256 GB Storage, White)", "Nandilath G Mart", "Apple"),
        rec("Apple iPhone 17 (Black, 256 GB) (8 GB RAM)", "Oxygen", "Apple"),
    ])
    assert keys(groups) == {"apple|iphone17|||256|": ["Nandilath G Mart", "Oxygen", "myG"]}
    assert not skipped


def test_partial_specs_skipped_for_other_brands():
    _, _, skipped = match([rec("Vivo Y05 | 64 GB | Blue", "myG", "Vivo")])
    assert skipped[0]["skip_reason"] == "specs_partial"


def test_feature_phones_match_on_ta_code():
    groups, _, skipped = match([
        rec("Nokia 110 Power Keypad Phone | Dual SIM | Purple | TA-1751", "myG", "Nokia"),
        rec("Nokia 110 Power Keypad Phone | Dual SIM | Blue | TA-1751", "myG", "Nokia"),
        rec("Nokia 123 Shield DS | Green | TA-1742", "myG", "Nokia"),
        rec("Nokia 130 Music Dual Sim | Purple | NM", "myG", "Nokia"),
    ])
    assert set(keys(groups)) == {"nokia|ta|ta-1751", "nokia|ta|ta-1742"}
    assert len(next(g for g in groups if g["ta_code"] == "TA-1751")["listings"]) == 2
    assert skipped[0]["skip_reason"] == "no_specs_no_ta_code"


def test_ta_code_with_two_models_goes_to_review():
    groups, review, _ = match([
        rec("Nokia 110 | Blue | TA-1751", "myG", "Nokia"),
        rec("Nokia 105 | Blue | TA-1751", "Oxygen", "Nokia"),
    ])
    assert not groups and review[0]["reason"] == "ta_code_model_differs"


def test_untrusted_brand_excluded():
    _, _, skipped = match([
        rec("Galaxy A07 5G (Black, 128 GB) (4 GB RAM)", brand=None, status="unknown"),
        rec("Samsung Symphony A07 (4+128GB)", brand=None, status="review"),
    ])
    assert sorted(s["skip_reason"] for s in skipped) == ["brand_review", "brand_unknown"]


def test_price_spread_flagged_but_kept():
    groups, review, _ = match([
        rec("vivo Y11 5G (Blue, 64 GB) (4 GB RAM)", "Oxygen", "Vivo", price=10000),
        rec("Vivo Y11 5G (4GB/64GB Storage, Blue)", "Nandilath G Mart", "Vivo", price=13000),
    ])
    assert len(groups) == 1 and review[0]["reason"] == "price_spread"


def test_deterministic_regardless_of_order():
    records = [
        rec("realme C83 5G (Green, 64 GB) (4 GB RAM)", "Oxygen", "realme"),
        rec("Realme C83 5G | 4GB | 64GB | Green | NM", "myG", "realme"),
        rec("Realme C83 5G (4GB Ram/64GB Storage, Purple)", "Nandilath G Mart", "realme"),
        rec("Realme C83 5G | 6GB | 128GB | Purple | NM", "myG", "realme"),
    ]
    first = match(records)
    shuffled = records[:]
    random.Random(1).shuffle(shuffled)
    assert match(shuffled) == first


# ---- 1.2: name layouts -------------------------------------------------------

def test_category_path_prefix_matches_other_formats():
    groups, review, _ = match([
        rec("XIAOMI:SMART PHONES:REDMI 15C 6/128GB 5G MOONLIGHT BLUE (NEW)", "Oxygen", "Xiaomi"),
        rec("Redmi 15C 5G (6GB RAM/128GB Storage, Dusk Purple)", "Nandilath G Mart", "Xiaomi"),
    ])
    assert keys(groups) == {"xiaomi|redmi15c|5g|6|128|": ["Nandilath G Mart", "Oxygen"]}
    assert not review


def test_category_path_with_apple():
    groups, _, _ = match([
        rec("APPLE:SMART PHONES:IPHONE 17 256GB BLACK MG6J4HN/A (NEW)", "Oxygen", "Apple"),
        rec("Apple iPhone 17 | 256 GB | Black | NM", "myG", "Apple"),
    ])
    assert keys(groups) == {"apple|iphone17|||256|": ["Oxygen", "myG"]}


def test_unitless_sizes_read_only_for_real_sizes():
    r = parse_listing(rec("VIVO:SMART PHONES:S2 FE 6/128 TITAN BLACK", brand="Vivo"))
    assert (r["model"], r["ram_gb"], r["storage_gb"]) == ("s2 fe", 6, 128)
    # 5/100 is not a RAM / storage pair, so nothing is read from it
    odd = parse_listing(rec("Testco Zed 5/100 Black", brand="Testco"))
    assert odd["ram_gb"] is None and odd["storage_gb"] is None
    assert odd["skip_reason"] == "no_specs_no_ta_code"


def test_model_ends_at_spaced_dash():
    a = parse_listing(rec("REDMI A7 Pro 5G - Sunset Orange, 64 GB, 4 GB RAM", brand="Xiaomi"))
    b = parse_listing(rec("REDMI A7 Pro 5G (Black, 64 GB) (4 GB RAM)", brand="Xiaomi"))
    assert a["model_key"] == b["model_key"] == "redmia7pro"
    assert parse_listing(rec("Testco X-Pro 5G (Black, 64 GB) (4 GB RAM)", brand="Testco"))[
        "model"] == "x pro"  # an unspaced hyphen is part of the model

"""Unknown store categories: skip those products, and hold back only a store
that has too many of them."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "data_processing"))

from normalizer import ALIASES_FILE, NAME_RULES_FILE, TAXONOMY_FILE, Normalizer, load_json
from run_normalization import normalize_dir

KNOWN = ("Pittappillil", "Kitchen Appliances", "Air Fryer")
OTHER = ("Oxygen", "LED TV", None)


@pytest.fixture
def norm():
    return Normalizer(load_json(TAXONOMY_FILE), load_json(ALIASES_FILE), load_json(NAME_RULES_FILE))


def products(n, shop, cat, sub, tag="p"):
    return [{"name": f"{tag} {i}", "price": 1000, "url": f"https://x/{shop}/{tag}/{i}",
             "availability": "In stock", "shop": shop, "category": cat, "subcategory": sub}
            for i in range(n)]


@pytest.fixture
def dirs(tmp_path):
    d = {k: tmp_path / k for k in ("cleaned", "out", "tmp")}
    d["cleaned"].mkdir()
    d["report"] = tmp_path / "report.json"
    return d


def write(path, records):
    path.write_text(json.dumps(records))


def run(norm, d):
    return normalize_dir(norm, d["cleaned"], d["out"], d["tmp"], d["report"])


def test_a_new_category_skips_only_its_products(norm, dirs):
    write(dirs["cleaned"] / "pittappillil_kitchen.json",
          products(99, *KNOWN) + products(1, "Pittappillil", "Kitchen Appliances", "Brand New Pan", "new"))
    write(dirs["cleaned"] / "oxygen_kitchen.json", products(10, *OTHER))

    report = run(norm, dirs)

    assert len(json.loads((dirs["out"] / "pittappillil_kitchen.json").read_text())) == 99
    assert len(json.loads((dirs["out"] / "oxygen_kitchen.json").read_text())) == 10
    assert report["skipped"] == 1 and report["held_back_shops"] == []
    (combo,) = report["unmapped_combinations"]
    assert combo["subcategory"] == "Brand New Pan" and combo["count"] == 1


def test_a_store_over_the_limit_keeps_its_previous_data_and_others_update(norm, dirs):
    dirs["out"].mkdir()
    old = products(50, *KNOWN, tag="old")
    write(dirs["out"] / "pittappillil_kitchen.json", old)
    write(dirs["out"] / "oxygen_kitchen.json", products(3, *OTHER, tag="old"))

    write(dirs["cleaned"] / "pittappillil_kitchen.json",
          products(90, *KNOWN) + products(10, "Pittappillil", "Renamed", "Everything", "new"))
    write(dirs["cleaned"] / "oxygen_kitchen.json", products(10, *OTHER))

    report = run(norm, dirs)

    assert json.loads((dirs["out"] / "pittappillil_kitchen.json").read_text()) == old
    assert len(json.loads((dirs["out"] / "oxygen_kitchen.json").read_text())) == 10
    assert report["held_back_shops"] == [{"shop": "Pittappillil", "skipped": 10, "products": 100}]
    assert report["kept_previous_files"] == ["pittappillil_kitchen.json"]


def test_exactly_at_the_limit_is_not_held_back(norm, dirs):
    write(dirs["cleaned"] / "pittappillil_kitchen.json",
          products(95, *KNOWN) + products(5, "Pittappillil", "Kitchen Appliances", "Brand New Pan", "new"))
    report = run(norm, dirs)
    assert report["held_back_shops"] == [] and report["skipped"] == 5


def test_the_limit_counts_all_of_a_stores_files(norm, dirs):
    # 6 unknown in a small file, but 6 of 200 across the store is only 3%.
    write(dirs["cleaned"] / "pittappillil_a.json", products(190, *KNOWN))
    write(dirs["cleaned"] / "pittappillil_b.json",
          products(4, *KNOWN, tag="b") + products(6, "Pittappillil", "Kitchen Appliances", "Brand New Pan", "new"))
    report = run(norm, dirs)
    assert report["held_back_shops"] == []
    assert len(json.loads((dirs["out"] / "pittappillil_b.json").read_text())) == 4

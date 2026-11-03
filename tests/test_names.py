import pytest

from api.names import shown_name
from api.schemas import DealOut


@pytest.mark.parametrize("raw, shown", [
    ("ASUS:LAPTOPS: TUF A15 FA506NCQ-IN080W RYZEN 7 170 | 16GB", "ASUS TUF A15 FA506NCQ-IN080W RYZEN 7 170 | 16GB"),
    ("LG:REFRIGERATOR:GLT2526XWDS.DDSZEBN 251 LTR DAZZLE STEEL", "LG GLT2526XWDS.DDSZEBN 251 LTR DAZZLE STEEL"),
    ("APPLE:SMART PHONES:IPHONE 17 [256 GB]", "APPLE IPHONE 17 [256 GB]"),
    ("SAMSUNG:SMART PHONES:SAMSUNG GALAXY A06", "SAMSUNG GALAXY A06"),
    ("HAVELLS:AIR FRYER:Prolife Vista Digital 4.2L Air Fryer", "HAVELLS Prolife Vista Digital 4.2L Air Fryer"),
])
def test_store_filing_is_taken_off(raw, shown):
    assert shown_name(raw) == shown


@pytest.mark.parametrize("name", [
    "Samsung Galaxy A06 5G 4GB 64GB Black",
    "Samsung Galaxy A06 5G (6GB/128GB) Gold",
    "Ratio 16:9 Monitor",
    "Sony Bravia: 55 inch: 4K",  # not in capitals, not a store's filing
    "ASUS:LAPTOPS:",  # nothing after it: leave as is
])
def test_other_names_are_left_alone(name):
    assert shown_name(name) == name


def test_api_output_uses_the_shown_name():
    deal = DealOut(kind="price_drop", name="ASUS:LAPTOPS: TUF A15", brand="ASUS", retailer="Oxygen",
                   price=1, compared_price=2, compared_retailer=None, saving=1, label="x",
                   checked_at="2026-11-03T00:00:00Z")
    assert deal.name == "ASUS TUF A15"

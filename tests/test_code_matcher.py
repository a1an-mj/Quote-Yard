"""Model-code matching: every case below is a real name from the store data."""
import pytest

from matching.code_matcher import extract_code, extract_size, match

TV = "Television"
WM = "Washing Machine"


def rec(shop, name, price=10000, brand="LG", status="matched"):
    return {"shop": shop, "url": f"https://{shop}/{name}", "name": name, "price": price,
            "brand": brand, "brand_status": status}


@pytest.mark.parametrize("name,brand,code", [
    ("LG NANO 4K UHD TV | 139 cm (55) | Black | 55NU880BPLA", "LG", "55NU880BPLA"),
    ("LG:LED TV:65NU880BPLA.ATR 164 CM (65 INCH) 4K UHD SMART", "LG", "65NU880BPLA"),
    ("LG 139cm (55 Inches) 4K Ultra HD OLED Smart TV, OLED 55B56LA", "LG", "OLED55B56LA"),
    ("Sony Bravia 3 4K Ultra HD Smart LED Google TV | 139 cm (55 Inch) | K 55S30", "Sony", "K55S30"),
    ("Sony 139cm (55 Inch) 4K Ultra HD Smart Google TV (Bravia 3,K-55S30)", "Sony", "K55S30"),
    ("SAMSUNG 43 INCH UHD 4K SMART LED TV, UA43U8400HU", "Samsung", "UA43U8400HU"),
    ("Samsung 1.08m (43 Inch) Crystal 4K UHD Smart Led TV, 2026 Model (UA43U8400HULXL)",
     "Samsung", "UA43U8400HU"),
    ("Samsung 1.63m (65 Inch) Crystal 4K UHD Smart TV, 2026 Model (65U8300HU)",
     "Samsung", "UA65U8300HU"),
    ("Samsung WT90C4260GG/TL 9KG Top Load Washing Machine Grey", "Samsung", "WT90C4260GG"),
    ("Samsung 9.0 kg 5 Star Semi Automatic Washing Machine (WT90C4260GG, Gray)", "Samsung", "WT90C4260GG"),
    ("Samsung WD12FG5B34BBTL 12/7KG Washer Dryer Silver", "Samsung", "WD12FG5B34BB"),
    ("LG Fully Automatic Top Load Washing Machine | 8 Kg | T80V4MB1S ABMQEIL", "LG", "T80V4MB1S"),
    ("IFB 8 kg 5 Star Washing Machine, RPM 1200 (Senator BXN 8012K CMS, Black)", "IFB", "BXN8012K"),
    ("IFB 8KG FRONT LOAD WASHING MACHINE SENATOR BXN 8012K CMS", "IFB", "BXN8012K"),
    ("IFB 9/6/3KG FULLY AUTOMATIC FRONT LOAD WASHING MACHINE, WDR EXECUTIVE ZBN", "IFB", None),
    ("Godrej 8 kg Top Load (WTEON VLVT 80 5.0 FDTS MTBK, Metallic Black)", "Godrej", "WTEONVLVT8050FDTSMTBK"),
    ("Godrej Top Load | 8 kg | Metallic Black | WTEON VLVT 80 5.0 FDTS MTBK", "Godrej", "WTEONVLVT8050FDTSMTBK"),
    ("Godrej WTEON ADR+ 70 5.0 FDUN GPGR Fully Automatic Top Load Washing Machine | 7 Kg", "Godrej", "WTEONADR7050FDUNGPGR"),
    ("Godrej Semi | 8 kg | WS EDGE ULT 80 5.0 DB2 M MIGR", "Godrej", "WSEDGEULT8050DB2MMIGR"),
    ("WHIRLPOOL 8 KG FULLY AUTOMATIC TOP LOAD WASHING MACHINE, STAINWASH PRO GREY 10YrMW", "Whirlpool", None),
    ("Whirlpool 9Kg 5Star Semi Automatic Top Load Washing Machine (Ace XL, Grey Dazzle)", "Whirlpool", None),
    ("IFB 10 kg Washing Machine Rpm1400 (Executive)", None, None),
    ("Samsung 189 L 5 Star Refrigerator (RR21H2H25BR, Begonia Red)", "Samsung", "RR21H2H25BR"),
    ("Samsung Refrigerator | 189 L | Begonia Red | RR21H2H25BR/HL", "Samsung", "RR21H2H25BR"),
    ("SAMSUNG 236 LITRE FROST FREE 2 STAR RT-40H28W2PNL REFRIGERATOR", "Samsung", "RT40H28W2P"),
    ("Godrej 244 L 2 Star (RT EONVALOR 280BN RI FS ST, Fossil Steel)", "Godrej", "RTEONVALOR280BNRIFSST"),
    ("Godrej 244 L 2 Star (RT EONCRYSTAL 280BN RI OB, Onyx Black)", "Godrej", "RTEONCRYSTAL280BNRIOB"),
    ("Godrej RD Emarvel 207CN TDF Direct Cool Single Door Refrigerator | 184 L", "Godrej", "RDEMARVEL207CNTDF"),
    ("LIEBHERR 191L DIRECT COOL REFRIGERATOR, DNBsiE 1911 I01 20", "Liebherr", "DNBSIE1911"),
    ("Liebherr Direct Cool Single Door Fridge | 191L | 5 Star | Silver Steel | DNBsiE 1911", "Liebherr", "DNBSIE1911"),
    ("Impex 164 cm (65 Inch) 4k QD-Mini Led Google Smart TV (EVOQ65S4MLC3)", "Impex", "65S4MLC3"),
    ("IMPEX 55 Inch 4K QLED Google Smart TV, Dolby Vision | Dolby ATMOS (evoQ 55S4QLC3)",
     "Impex", "55S4QLC3"),
    ("HAIER:LED TV:43P7 PRO 109 CM (43 INCH) QLED SMART", "Haier", "43P7PRO"),
    ("TCL 4K UHD QD-Mini LED Smart Google TV | 139 cm (55 inch) | 55A400 PRO", "TCL", "55A400PRO"),
    ("TCL 80 CM (32INCH) HD QLED GOOGLE, 32S4k TELEVISION", "TCL", "32S4K"),
])
def test_extract_code(name, brand, code):
    assert extract_code(name, brand) == code


@pytest.mark.parametrize("name", [
    "GDOT WESTERN WTS SMART LED TV | 108 cm (43 Inch)",
    "Xiaomi A Pro QLED TV | 81.28 cm (32 inch) | Black",
    "MR LED Smart TV | 109 cm (43 Inch) | Full HD IPS Display | 120Hz | HDR10",
    "TCL 55 Inch 4K UHD Premium QD-MiniLED Google TV (C6K)",
    "Sony Bravia 2M2 Series 4K Ultra HD Smart LED TV",
])
def test_names_without_a_code(name):
    assert extract_code(name) is None


def test_size_comes_from_inches_not_a_wrong_cm():
    assert extract_size("Hisense 80cm (43 Inch) Full HD Smart Led TV (43E4S)", TV) == 43
    assert extract_size("LG NANO 4K UHD TV | 139 cm (55) | Black", TV) is None


def test_washing_machine_sizes():
    assert extract_size("LG 7.5 Kg Semi Automatic, P-7510RRAZ", WM) == 7.5
    assert extract_size("LG | 8.0 Kg | T80", WM) == extract_size("LG 8KG FRONT LOAD", WM) == 8
    assert extract_size("IFB 9/6/3KG FRONT LOAD", WM) is None
    groups, _, _ = match([rec("myG", "LG Top Load | 7.5 Kg | T75VBMB1S")], WM)
    assert groups[0]["name"] == "LG 7.5 kg Washing Machine T75VBMB1S"
    assert groups[0]["size_label"] == "7.5 kg"


def test_whirlpool_refrigerators_are_skipped():
    groups, _, skipped = match([
        rec("myG", "Whirlpool Fridge | 235L | IF INV ELT DF278", brand="Whirlpool"),
        rec("Pittappillil", "WHIRLPOOL 235 Litre NEO DF278 PRM", brand="Whirlpool"),
    ], "Refrigerator")
    assert not groups and [r["skip_reason"] for r in skipped] == ["no_model_code"] * 2


def test_refrigerator_sizes():
    for name in ("LG 251L FROST FREE", "LG | 251 L | X", "LG 251 LITRE STAR", "LG:FRIDGE:X 251 LTR"):
        assert extract_size(name, "Refrigerator") == 251


def test_stores_written_differently_become_one_product():
    groups, review, skipped = match([
        rec("Oxygen", "LG:LED TV:43NU880BPLA.ATR 108 CM (43 INCH) SMART"),
        rec("Pittappillil", "LG 43 INCH UHD 4K SMART LED TV, 43NU880BPLA.ATR"),
        rec("myG", "LG Nano 4K UHD Smart TV | with Dolby Atmos | 108 cm (43) | 43NU880BPLA"),
    ], TV)
    assert [g["model_code"] for g in groups] == ["43NU880BPLA"]
    assert groups[0]["shops"] == ["Oxygen", "Pittappillil", "myG"]
    assert groups[0]["size"] == 43
    assert groups[0]["name"] == "LG 43 inch TV 43NU880BPLA"
    assert not review and not skipped


def test_near_codes_stay_apart():
    groups, _, _ = match([
        rec("Pittappillil", "SONY 108 CM (43 Inch) 4K TV, K-43S22GM2", brand="Sony"),
        rec("myG", "Sony Bravia | 43 inches | K-43S22M2", brand="Sony"),
        rec("Nandilath G Mart", "TCL 55 Inch TV (55A400)", brand="TCL"),
        rec("myG", "TCL 55 Inch TV | 55A400 PRO", brand="TCL"),
    ], TV)
    assert sorted(g["model_code"] for g in groups) == ["55A400", "55A400PRO", "K43S22GM2", "K43S22M2"]


def test_same_code_from_two_brands_stays_apart():
    groups, _, _ = match([
        rec("myG", "TV | 32 inch | ABC1234", brand="LG"),
        rec("Oxygen", "TV | 32 inch | ABC1234", brand="TCL"),
    ], TV)
    assert len(groups) == 2


def test_different_sizes_go_to_review_unmerged():
    groups, review, _ = match([
        rec("myG", "LG TV | 43 inch | ABC1234"),
        rec("Oxygen", "LG TV | 55 inch | ABC1234"),
    ], TV)
    assert not groups
    assert review[0]["reason"] == "size_conflict"


def test_big_price_gap_goes_to_review_unmerged():
    groups, review, _ = match([
        rec("myG", "LG TV | 43 inch | ABC1234", price=10000),
        rec("Oxygen", "LG TV | 43 inch | ABC1234", price=12501),
    ], TV)
    assert not groups
    assert review[0]["reason"] == "price_spread"


def test_possible_miss_is_reported_not_merged():
    groups, review, _ = match([
        rec("Nandilath G Mart", "Sony 55 inches TV (K-55XR70)", brand="Sony"),
        rec("myG", "Sony TV | 55 inch | K-55XR70M2", brand="Sony"),
    ], TV)
    assert len(groups) == 2
    assert [r["reason"] for r in review] == ["possible_miss"]


def test_skips_are_explained():
    _, _, skipped = match([
        rec("myG", "GDOT WESTERN WTS SMART LED TV | 108 cm (43 Inch)"),
        rec("myG", "LG TV | ABC1234", status="review"),
    ], TV)
    assert sorted(r["skip_reason"] for r in skipped) == ["brand_review", "no_model_code"]


def test_order_does_not_change_the_result():
    records = [rec("myG", "LG TV | 43 inch | ABC1234"), rec("Oxygen", "LG TV | ABC1234")]
    assert match(records, TV)[0][0]["match_key"] == match(records[::-1], TV)[0][0]["match_key"]
    assert match(records, TV)[0][0]["match_key"] == "television|lg|abc1234"

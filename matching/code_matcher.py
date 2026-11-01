#!/usr/bin/env python
"""Phase 9: conservative matching on manufacturer model codes.

Two listings match only when brand and model code agree, and their sizes do
not contradict each other. Anything doubtful goes to the review section of the
report, never into a group by guess. Listings without a recognisable code are
skipped. Writes only to reports/. No database.

Rules (CODE_MATCHING_VERSION 1.2):
  - Only brand_status "matched" listings take part.
  - The code is the last word in the name with both letters and digits, at
    least 4 characters, that is not a measurement or a feature ("55Inch", "4K",
    "HDR10", "1400Rpm", "12/7KG", the warranty word "10YrMW") and is not
    followed by "Series".
  - Dashes and slashes are ignored, so "K-55S30" == "K55S30". Colour-specific
    codes stay separate products.
  - A split code is joined only for the prefixes seen in the data ("K 55S30",
    "OLED 55B56LA"); PRO / MAX / PLUS / ULTRA straight after a code is part of it.
  - Brand rules seen on the same products in the data: LG's ".ATR" ending,
    Samsung's "LXL", "TL", "HL" and "NL" endings and missing "UA" prefix, Impex's "EVOQ"
    prefix. IFB ("BXN 8012K") and Godrej ("WTEON VLVT 80 5.0 FDTS MTBK") write
    their codes as several words, which are joined; so does Liebherr ("DNBsiE 1911").
  - Whirlpool refrigerators are skipped: one word such as "DF278" covers
    different product lines.
  - Different sizes under one code, or prices apart by more than PRICE_SPREAD_LIMIT,
    send the whole group to review, unmerged.
  - Possible misses (one code inside another) are reported, never merged.

Run from the repo root:
    python -m matching.code_matcher --type Television
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from matching.extract_phones import load_records

CODE_MATCHING_VERSION = "1.2"
ROOT = Path(__file__).resolve().parent.parent
PRICE_SPREAD_LIMIT = 1.25
MIN_CODE_LENGTH = 4

SIZE_PATTERNS = {
    "Television": (re.compile(r"(\d{2,3})\s*(?:-|\")?\s*inch(?:es)?\b", re.I), "inch"),
    # Not "9/6/3KG" or "12/7KG": those are wash / dry capacities.
    "Refrigerator": (re.compile(r"(?<![\d./])(\d{2,4})\s*(?:l|ltrs?|litres?)\b", re.I), "L"),
    "Washing Machine": (re.compile(r"(?<![\d./])(\d{1,2}(?:\.\d)?)\s*kg\b(?!\s*/\d)", re.I), "kg"),
}
SHORT_NAMES = {"Television": "TV"}

TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9./\-]*[A-Za-z0-9]")
NOT_A_CODE = re.compile(
    r"^(?:\d+(?:\.\d+)?(?:cm|m|mm|inch|inches|hz|k|w|ch|l|ltr|kg|gb|tb|ton|star)"
    r"|hdr\d+|gen\d+|rpm\d+|\d+rpm|[\d./]+kg|\d+y(?:r|m|rm|mw|rmw)?)$",
    re.I,
)
SPLIT_PREFIX = re.compile(r"\b(K|OLED)\s+(\d{2}[A-Za-z])")
IFB_CODE = re.compile(r"\b([A-Z]{3})\s+(\d{4}K?H?)\b")
GODREJ_CODE = re.compile(
    r"\b(?:W(?:FEON|TEON|SEDGE|S\s+EDGE)|R[DST]\s+E[A-Z]+)\b[^|,()]*?"
    r"(?=\s+(?:Fully|Direct)\b|\s*[|,()]|\s*$)", re.I)
LIEBHERR_CODE = re.compile(r"\b([A-Za-z]{5,6})\s+(\d{4})\b")
NO_RELIABLE_CODE = {("Refrigerator", "Whirlpool")}
VARIANT_AFTER_CODE = {"pro", "max", "plus", "ultra"}
BRAND_RULES = {
    "LG": lambda code: code.split(".", 1)[0],
    "Samsung": lambda code: re.sub(r"^(?=\d)", "UA", re.sub(r"(?:LXL|TL|HL|NL)$", "", code)),
    "Impex": lambda code: re.sub(r"^EVOQ(?=\d)", "", code),
}


def is_code_word(word):
    return (
        len(re.sub(r"[^A-Za-z0-9]", "", word)) >= MIN_CODE_LENGTH
        and bool(re.search(r"[A-Za-z]", word))
        and bool(re.search(r"\d", word))
        and not NOT_A_CODE.match(word)
    )


def extract_code(name, brand=None):
    """Return the normalised model code in a name, or None."""
    if brand == "Godrej":
        found = GODREJ_CODE.search(name)
        if found:
            return re.sub(r"[^A-Za-z0-9]", "", found.group()).upper()
    if brand == "Liebherr":
        name = LIEBHERR_CODE.sub(r"\1\2", name)
    if brand == "IFB":
        name = IFB_CODE.sub(r"\1\2", name)
    words = TOKEN.findall(SPLIT_PREFIX.sub(r"\1\2", name))
    for i in range(len(words) - 1, -1, -1):
        word = words[i]
        following = words[i + 1].casefold() if i + 1 < len(words) else ""
        if following == "series" or not is_code_word(word):
            continue
        code = word.upper()
        code = BRAND_RULES.get(brand, lambda c: c)(code)
        code = re.sub(r"[-/]", "", code)
        if following in VARIANT_AFTER_CODE:
            code += following.upper()
        return code
    return None


def extract_size(name, product_type):
    pattern = SIZE_PATTERNS.get(product_type)
    if pattern is None:
        return None
    found = pattern[0].search(name)
    return float(found.group(1)) if found else None


def parse_listing(rec, product_type):
    brand = rec.get("brand")
    out = {
        "shop": rec["shop"], "url": rec["url"], "name": rec["name"],
        "price": rec.get("price"), "brand": brand, "brand_status": rec.get("brand_status"),
        "model_code": None if (product_type, brand) in NO_RELIABLE_CODE
                      else extract_code(rec["name"], brand),
        "size": extract_size(rec["name"], product_type),
        "box_note": None, "skip_reason": None,
    }
    if out["brand_status"] != "matched":
        out["skip_reason"] = f"brand_{out['brand_status']}"
    elif out["model_code"] is None:
        out["skip_reason"] = "no_model_code"
    elif out["price"] is None:
        out["skip_reason"] = "no_price"
    return out


def display_name(brand, code, size, product_type):
    unit = SIZE_PATTERNS[product_type][1] if size and product_type in SIZE_PATTERNS else None
    label = SHORT_NAMES.get(product_type, product_type)
    middle = f"{size:g} {unit} {label}" if unit else label
    return f"{brand} {middle} {code}"


def match(records, product_type):
    """Return (groups, review, skipped). Same input gives the same output in any order."""
    parsed = sorted((parse_listing(r, product_type) for r in records),
                    key=lambda r: (r["shop"], r["url"]))
    skipped = [r for r in parsed if r["skip_reason"]]

    buckets = defaultdict(list)
    for r in parsed:
        if not r["skip_reason"]:
            buckets[(r["brand"], r["model_code"])].append(r)

    groups, review = [], []
    for (brand, code), members in sorted(buckets.items()):
        sizes = {m["size"] for m in members if m["size"] is not None}
        prices = [m["price"] for m in members]
        if len(sizes) > 1:
            review.append({"reason": "size_conflict", "listings": members,
                           "detail": f"{brand} {code}: sizes {sorted(sizes)}"})
            continue
        if max(prices) > min(prices) * PRICE_SPREAD_LIMIT:
            review.append({"reason": "price_spread", "listings": members,
                           "detail": f"{brand} {code}: {min(prices)}..{max(prices)}"})
            continue
        size = next(iter(sizes), None)
        groups.append({
            "match_key": f"{product_type}|{brand}|{code}".casefold(),
            "matching_version": CODE_MATCHING_VERSION,
            "brand": brand, "model": code, "model_code": code, "size": size,
            "size_label": f"{size:g} {SIZE_PATTERNS[product_type][1]}" if size else None,
            "name": display_name(brand, code, size, product_type),
            "shops": sorted({m["shop"] for m in members}),
            "min_price": min(prices), "max_price": max(prices),
            "listings": members,
        })
    review += _possible_misses(groups)
    return groups, review, skipped


def _possible_misses(groups):
    """Codes from one brand, one inside the other, at different shops. Never merged."""
    out = []
    by_brand = defaultdict(list)
    for g in groups:
        by_brand[g["brand"]].append(g)
    for gs in by_brand.values():
        for i, a in enumerate(gs):
            for b in gs[i + 1:]:
                short, long = sorted((a, b), key=lambda g: (len(g["model_code"]), g["model_code"]))
                if short["model_code"] not in long["model_code"]:
                    continue
                if short["size"] and long["size"] and short["size"] != long["size"]:
                    continue
                if set(a["shops"]) == set(b["shops"]) and len(a["shops"]) == 1:
                    continue
                out.append({"reason": "possible_miss", "listings": short["listings"] + long["listings"],
                            "detail": f"{short['name']}  vs  {long['name']}"})
    return out


def build_report(groups, review, skipped, total, product_type):
    L = []
    add = L.append
    multi = [g for g in groups if len(g["shops"]) >= 2]
    add(f"{product_type} matching report (version {CODE_MATCHING_VERSION}): {total} listings\n")
    add("== Summary ==")
    add(f"  products (groups):           {len(groups)}")
    add(f"  ... sold by 2+ retailers:    {len(multi)}")
    add(f"  listings in groups:          {sum(len(g['listings']) for g in groups)}")
    add(f"  listings in cross-retailer groups: {sum(len(g['listings']) for g in multi)}")
    add(f"  listings skipped:            {len(skipped)}")
    add(f"  review items:                {len(review)}")
    add("  groups by number of retailers: " + ", ".join(
        f"{k}={v}" for k, v in sorted(Counter(len(g["shops"]) for g in groups).items())))
    add("")

    add(f"== Cross-retailer groups ({len(multi)}) ==")
    for g in multi:
        add(f"  {g['name']}   {g['min_price']}..{g['max_price']}")
        for m in g["listings"]:
            add(f"      [{m['shop']}] {m['price']:>7}  {m['name']}")
    add("")

    add(f"== Review ({len(review)}) ==")
    for item in sorted(review, key=lambda x: (x["reason"], x["detail"])):
        add(f"  {item['reason']}: {item['detail']}")
        for m in item["listings"]:
            add(f"      [{m['shop']}] {m['price']:>7}  {m['name']}")
    add("")

    add(f"== Skipped ({len(skipped)}) ==")
    for r in skipped:
        add(f"  {r['skip_reason']}: [{r['shop']}] {r['name']}")
    add("")

    add(f"== Single-retailer groups ({len(groups) - len(multi)}) ==")
    for g in groups:
        if len(g["shops"]) == 1:
            add(f"  [{g['shops'][0]}] {g['name']}  ({len(g['listings'])} listing(s))  <- {g['listings'][0]['name']}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--type", required=True)
    ap.add_argument("--data-dir", default=str(ROOT / "branded_data"))
    ap.add_argument("--out-dir", default=str(ROOT / "reports"))
    args = ap.parse_args()

    records = load_records(args.data_dir, args.type)
    if not records:
        raise SystemExit(f"No '{args.type}' records found in {args.data_dir}")
    groups, review, skipped = match(records, args.type)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    slug = args.type.casefold().replace(" ", "_")
    (out / f"{slug}_matches.json").write_text(json.dumps(
        {"matching_version": CODE_MATCHING_VERSION, "groups": groups,
         "review": review, "skipped": skipped}, indent=2, ensure_ascii=False), encoding="utf-8")
    report = build_report(groups, review, skipped, len(records), args.type)
    (out / f"{slug}_match_report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()

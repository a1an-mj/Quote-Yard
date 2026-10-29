#!/usr/bin/env python
"""Phase 5, step 2: conservative matching of mobile-phone listings.

Groups listings from branded_data/*.json into candidate canonical products.
Two listings match only when brand, model, RAM, storage and package all agree
(network too, see below). Colour is never part of the key. Anything that
cannot be decided goes to the review section of the report, never into a
group by guess. Writes only to reports/. No database.

Rules (MATCHING_VERSION 1.1):
  - Only brand_status "matched" listings take part.
  - Model key: name head (before "|", "(" or the first size), casefolded,
    punctuation removed, brand word and filler words dropped, then joined
    without spaces, so "V70FE" == "V70 FE". For Samsung "galaxy" is optional.
  - Network (2G-5G, LTE = 4G) is read from the whole name. A listing without
    one joins its model's network if the data shows only one network for that
    model; if the model appears with two networks it goes to review.
  - Bundle words ("photographer kit") are part of the key, so a bundle never
    merges with the plain phone. Box-content words ("without adapter") are
    not: the listing keeps them as box_note and the group lists them.
  - Retailer-specific words verified against the retailer's spec table are
    dropped right after the brand (Pittappillil "SMART").
  - Apple: RAM is ignored (Apple does not publish it; storage decides).
  - Phones with neither RAM nor storage match on brand + TA model code.

Run from the repo root:
    python matching/phone_matcher.py
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from extract_phones import HEAD_SPLIT, extract_colour, load_records, parse_specs

MATCHING_VERSION = "1.1"
ROOT = Path(__file__).resolve().parent.parent

FILLER = {"smartphone", "smartphones", "mobile", "mobiles", "phone"}
OPTIONAL_LINE_WORDS = {"Samsung": {"galaxy"}}
RAM_IGNORED = {"Apple"}
# Tokens that name a different model, never noise ("S26" vs "S26 Ultra").
VARIANT_WORDS = {"pro", "max", "ultra", "plus", "fe", "lite", "mini", "neo",
                 "prime", "power", "fold", "flip", "edge", "note", "+"}
PRICE_SPREAD_LIMIT = 1.25

# Bundles add hardware, so they are part of the key: a kit never merges with the plain phone.
PACKAGES = [
    (re.compile(r"[-\s]*\b(?:with\s+)?photographer\s+kit\b", re.I), "photographer kit"),
]
# Box contents differ but the phone is the same: kept on the listing, not in the key.
BOX_NOTES = [
    (re.compile(r"\bwithout\s+(?:adapter|charger)\b", re.I), "without adapter"),
]
# Retailer-specific words that are not part of the model, each verified against the
# retailer's own spec table. Removed only straight after the brand word.
# Pittappillil: "NOTHING SMART 4B 5G" has Model "4B 5G"; "MOTOROLA SMART G06 POWER 4G"
# has Model "G06 POWER 4G" (checked on the product pages, 2026-10-29).
SHOP_WORDS_AFTER_BRAND = {"Pittappillil": {"smart"}}
NOTHING_PAREN = re.compile(r"\bphone\s*\(\s*(\w+)\s*\)", re.I)
NETWORK_ANY = re.compile(r"\b(?:([2345])G|(LTE))\b", re.I)
TA_CODE = re.compile(r"\bTA-?(\d{3,5})\b", re.I)


def _strip_labels(name, patterns):
    found = None
    for pat, label in patterns:
        if pat.search(name):
            found = label
            name = pat.sub(" ", name)
    return name, found


def _clean_name(name):
    """Return (name without package and box words, package or None, box note or None)."""
    name, package = _strip_labels(name, PACKAGES)
    name, box_note = _strip_labels(name, BOX_NOTES)
    name = NOTHING_PAREN.sub(r"Phone \1", name)
    return name, package, box_note


def _networks(name):
    return {f"{m.group(1)}G" if m.group(1) else "4G" for m in NETWORK_ANY.finditer(name)}


def parse_model_tokens(name, brand, shop=None):
    head = HEAD_SPLIT.split(name, 1)[0]
    head = NETWORK_ANY.sub(" ", head).casefold()
    head = re.sub(r"[^\w+\s]", " ", head)
    toks = [t for t in head.split() if t not in FILLER]
    if brand and toks and toks[0] == brand.casefold().split()[0]:
        toks = toks[1:]
        if toks and toks[0] in SHOP_WORDS_AFTER_BRAND.get(shop, set()):
            toks = toks[1:]
    optional = OPTIONAL_LINE_WORDS.get(brand, set())
    return [t for t in toks if t not in optional]


def parse_listing(rec):
    """Parse one branded record into the fields matching needs."""
    brand = rec.get("brand")
    name, package, box_note = _clean_name(rec["name"])
    toks = parse_model_tokens(name, brand, rec["shop"])
    ram, storage, spec_status, notes = parse_specs(name)
    nets = _networks(name)
    ta = TA_CODE.search(rec["name"])
    if brand in RAM_IGNORED:
        ram = None
    out = {
        "shop": rec["shop"], "url": rec["url"], "name": rec["name"],
        "price": rec.get("price"), "brand": brand, "brand_status": rec.get("brand_status"),
        "model": " ".join(toks), "model_key": "".join(toks),
        "network": next(iter(nets)) if len(nets) == 1 else None,
        "ram_gb": ram, "storage_gb": storage, "package": package, "box_note": box_note,
        "ta_code": f"TA-{ta.group(1)}" if ta else None,
        "colour": extract_colour(rec["name"]), "skip_reason": None,
    }
    if len(nets) > 1:
        out["skip_reason"] = "conflicting_network_words"
    elif out["brand_status"] != "matched":
        out["skip_reason"] = f"brand_{out['brand_status']}"
    elif not out["model_key"]:
        out["skip_reason"] = "model_empty"
    elif "storage_less_than_ram" in notes:
        out["skip_reason"] = "storage_less_than_ram"
    elif ram is None and storage is None:
        if not out["ta_code"]:
            out["skip_reason"] = "no_specs_no_ta_code"
    elif storage is None or (ram is None and brand not in RAM_IGNORED):
        out["skip_reason"] = "specs_partial"
    return out


def _key(r, network):
    if r["ram_gb"] is None and r["storage_gb"] is None:
        return (r["brand"], "ta", r["ta_code"])
    return (r["brand"], r["model_key"], network, r["ram_gb"], r["storage_gb"], r["package"])


def key_str(key):
    return "|".join("" if k is None else str(k) for k in key).casefold()


def display_name(members):
    heads = []
    for m in members:
        head = HEAD_SPLIT.split(_clean_name(m["name"])[0], 1)[0]
        head = re.sub(r"\s+", " ", NETWORK_ANY.sub(" ", head)).strip(" -,")
        for word in SHOP_WORDS_AFTER_BRAND.get(m["shop"], ()):
            head = re.sub(rf"^(\S+)\s+{word}\b", r"\1", head, flags=re.I)
        heads.append(head)
    nice = [h for h in heads if not h.isupper()] or heads
    head = max(nice, key=lambda h: (len(h.split()), h))
    r = members[0]
    parts = [head]
    if r["network"]:
        parts.append(r["network"])
    if r["package"]:
        parts.append(f"({r['package'].title()})")
    if r["ram_gb"] is None and r["storage_gb"] is None:
        parts.append(f"({r['ta_code']})")
    if r["storage_gb"] is not None:
        size = lambda g: f"{g // 1024} TB" if g >= 1024 and g % 1024 == 0 else f"{g} GB"
        spec = size(r["storage_gb"])
        if r["ram_gb"] is not None:
            spec = f"{r['ram_gb']} GB RAM, {spec}"
        parts.append(f"[{spec}]")
    return " ".join(parts)


def match(records):
    """Return (groups, review, skipped). Same input gives the same output in any order."""
    parsed = sorted((parse_listing(r) for r in records), key=lambda r: (r["shop"], r["url"]))
    skipped = [r for r in parsed if r["skip_reason"]]
    usable = [r for r in parsed if not r["skip_reason"]]
    review = []

    nets_by_model = defaultdict(set)
    for r in usable:
        if r["network"]:
            nets_by_model[(r["brand"], r["model_key"], r["package"])].add(r["network"])

    buckets = defaultdict(list)
    for r in usable:
        known = nets_by_model[(r["brand"], r["model_key"], r["package"])]
        if r["network"]:
            net = r["network"]
        elif len(known) <= 1:
            net = next(iter(known), None)
            r["network"] = net
        else:
            review.append({"reason": "network_ambiguous", "listings": [r],
                           "detail": f"no network in name; model seen as {sorted(known)}"})
            continue
        buckets[_key(r, net)].append(r)

    groups = []
    for key, members in sorted(buckets.items(), key=lambda kv: key_str(kv[0])):
        prices = [m["price"] for m in members]
        g = {
            "match_key": key_str(key), "matching_version": MATCHING_VERSION,
            "brand": members[0]["brand"], "model": members[0]["model"],
            "network": members[0]["network"], "ram_gb": members[0]["ram_gb"],
            "storage_gb": members[0]["storage_gb"], "package": members[0]["package"],
            "ta_code": members[0]["ta_code"] if key[1] == "ta" else None,
            "name": display_name(members),
            "shops": sorted({m["shop"] for m in members}),
            "box_notes": sorted({m["box_note"] for m in members if m["box_note"]}),
            "min_price": min(prices), "max_price": max(prices),
            "listings": members,
        }
        if key[1] == "ta" and len({m["model_key"] for m in members}) > 1:
            review.append({"reason": "ta_code_model_differs", "listings": members,
                           "detail": f"{g['ta_code']} used by {sorted({m['model'] for m in members})}"})
            continue
        if g["max_price"] > g["min_price"] * PRICE_SPREAD_LIMIT:
            review.append({"reason": "price_spread", "listings": members,
                           "detail": f"{g['min_price']}..{g['max_price']} in group {g['match_key']}"})
        groups.append(g)

    review += _possible_misses(groups)
    return groups, review, skipped


def _possible_misses(groups):
    """Pairs of groups at different shops that differ only by noise-looking words,
    or only by package. Reported for a human; never merged."""
    out = []
    spec = defaultdict(list)
    for g in groups:
        if g["ta_code"]:
            continue
        spec[(g["brand"], g["ram_gb"], g["storage_gb"])].append(g)
    for gs in spec.values():
        for i, a in enumerate(gs):
            for b in gs[i + 1:]:
                if set(a["shops"]) == set(b["shops"]) and len(a["shops"]) == 1:
                    continue
                ta, tb = set(a["model"].split()), set(b["model"].split())
                diff = ta ^ tb
                if a["model"].replace(" ", "") == b["model"].replace(" ", ""):
                    if a["package"] != b["package"]:
                        reason = "package_differs"
                    elif a["network"] != b["network"]:
                        reason = "network_differs"
                    else:
                        continue
                elif diff and all(not re.search(r"\d", t) and len(t) > 1 and "+" not in t
                                  and t not in VARIANT_WORDS for t in diff):
                    reason = "model_words_differ"
                else:
                    continue
                out.append({"reason": reason, "listings": a["listings"] + b["listings"],
                            "detail": f"'{a['name']}'  vs  '{b['name']}'"})
    return out


def build_report(groups, review, skipped, total):
    L = []
    add = L.append
    multi = [g for g in groups if len(g["shops"]) >= 2]
    grouped = sum(len(g["listings"]) for g in groups)
    add(f"Phone matching report (matching_version {MATCHING_VERSION}): {total} listings\n")
    add("== Summary ==")
    add(f"  canonical products (groups): {len(groups)}")
    add(f"  ... sold by 2+ retailers:    {len(multi)}")
    add(f"  listings in groups:          {grouped}")
    add(f"  listings in cross-retailer groups: {sum(len(g['listings']) for g in multi)}")
    add(f"  listings skipped:            {len(skipped)}")
    add(f"  review items:                {len(review)}")
    add("")
    add("  groups by number of retailers: " + ", ".join(
        f"{k}={v}" for k, v in sorted(Counter(len(g['shops']) for g in groups).items())))
    add("")

    add(f"== Cross-retailer groups ({len(multi)}) ==")
    for g in multi:
        add(f"  {g['name']}   key={g['match_key']}   {g['min_price']}..{g['max_price']}")
        for m in g["listings"]:
            note = f"   <box: {m['box_note']}>" if m["box_note"] else ""
            add(f"      [{m['shop']}] {m['price']:>7}  {m['name']}{note}")
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
            add(f"  [{g['shops'][0]}] {g['name']}  ({len(g['listings'])} listing(s))")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default=str(ROOT / "branded_data"))
    ap.add_argument("--out-dir", default=str(ROOT / "reports"))
    ap.add_argument("--type", default="Mobile Phone")
    args = ap.parse_args()

    records = load_records(args.data_dir, args.type)
    if not records:
        raise SystemExit(f"No '{args.type}' records found in {args.data_dir}")
    groups, review, skipped = match(records)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "phone_matches.json").write_text(json.dumps(
        {"matching_version": MATCHING_VERSION, "groups": groups,
         "review": review, "skipped": skipped}, indent=2, ensure_ascii=False), encoding="utf-8")
    report = build_report(groups, review, skipped, len(records))
    (out / "phone_match_report.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {out / 'phone_match_report.txt'} and {out / 'phone_matches.json'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Phase 5, step 1: READ-ONLY extraction report for mobile-phone listings.

Reads branded_data/*.json, keeps records whose product_type is "Mobile Phone",
parses model, network, RAM, storage and colour from the name, and reports how
cleanly that works. It writes only to reports/. No database, no matching.

Run from the repo root:
    python matching/extract_phones.py
    python matching/extract_phones.py --type "Mobile Phone" --data-dir branded_data
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILLER = {"smartphone", "smartphones", "mobile", "mobiles", "phone"}

# --- spec patterns (explicit first, positional guesses last) -----------------
RAM_EXPLICIT = re.compile(r"(?<![\d.])(\d{1,2})\s*GB\s*RAM\b", re.I)
STORAGE_EXPLICIT = re.compile(
    r"(?<![\d.])(\d{1,4})\s*(GB|TB)\s*(?:Storage|ROM|Internal)\b", re.I)
PLUS = re.compile(r"(?<![\w.])(\d{1,2})\s*(?:GB)?\s*\+\s*(\d{1,4})\s*(GB|TB)\b", re.I)
SLASH = re.compile(r"(?<![\w.])(\d{1,2})\s*(?:GB)?\s*/\s*(\d{1,4})\s*(GB|TB)\b", re.I)
BARE = re.compile(r"(?<![\d.])(\d{1,4})\s*(GB|TB)\b", re.I)
HEAD_SPLIT = re.compile(
    r"\||\(|(?<![\w.+])\d{1,4}\s*(?:GB|TB)\b|(?<![\w.+])\d{1,2}\s*[+/]\s*\d", re.I)
NETWORK = re.compile(r"\b([2345])G\b", re.I)


def to_gb(n, unit):
    return int(n) * 1024 if unit.upper() == "TB" else int(n)


def _take(pattern, text):
    """Return (match, text with the matched span blanked out)."""
    m = pattern.search(text)
    if not m:
        return None, text
    return m, text[:m.start()] + " " * (m.end() - m.start()) + text[m.end():]


def parse_specs(name):
    ram = storage = None
    notes = []
    text = name

    m, text = _take(RAM_EXPLICIT, text)
    if m:
        ram = int(m.group(1))
    m, text = _take(STORAGE_EXPLICIT, text)
    if m:
        storage = to_gb(m.group(1), m.group(2))

    if ram is None or storage is None:
        for pat in (PLUS, SLASH):
            m, text = _take(pat, text)
            if m:
                ram = ram if ram is not None else int(m.group(1))
                storage = storage if storage is not None else to_gb(m.group(2), m.group(3))
                break

    bare = [to_gb(a, b) for a, b in BARE.findall(text)]
    if bare:
        if ram is None and storage is None:
            if len(bare) == 1:
                storage = bare[0]
                notes.append("ram_missing")
            elif len(bare) == 2:
                if bare[0] < bare[1]:
                    ram, storage = bare
                else:
                    ram, storage = bare[1], bare[0]
                    notes.append("bare_sizes_reordered")
            else:
                notes.append("many_sizes")
        elif ram is not None and storage is None and len(bare) == 1:
            storage = bare[0]
        elif storage is not None and ram is None and len(bare) == 1 and bare[0] < storage:
            ram = bare[0]
        else:
            notes.append("extra_sizes")

    if ram is not None and storage is not None and storage < ram:
        notes.append("storage_less_than_ram")
    status = "ok" if (ram is not None and storage is not None) else (
        "partial" if (ram is not None or storage is not None) else "none")
    return ram, storage, status, notes


def extract_colour(name):
    parts = []
    for grp in re.findall(r"\(([^)]*)\)", name):
        parts += re.split(r"[,/]", grp)
    parts += name.split("|")[1:]
    if ")" in name:
        parts.append(name.rsplit(")", 1)[1])
    cands = []
    for p in parts:
        p = p.strip(" -,")
        if not p or not re.search(r"[A-Za-z]", p):
            continue
        if re.search(r"\d\s*(GB|TB)|\bRAM\b|storage|^\d+\s*\+\s*\d+", p, re.I):
            continue
        if re.fullmatch(r"[2345]G", p, re.I):
            continue
        cands.append(p)
    return cands[-1] if cands else None


def parse_model(name, brand):
    head = HEAD_SPLIT.split(name, 1)[0]
    m = NETWORK.search(head)
    network = m.group(0).upper() if m else None
    h = NETWORK.sub(" ", head).casefold()
    h = re.sub(r"[^\w+\s]", " ", h)
    toks = [t for t in h.split() if t not in FILLER]
    if brand and toks and toks[0] == brand.casefold().split()[0]:
        toks = toks[1:]
    return " ".join(toks), network


def parse_record(rec):
    name = rec["name"]
    brand = rec.get("brand")
    model, network = parse_model(name, brand)
    ram, storage, status, notes = parse_specs(name)
    if not model:
        notes.append("model_empty")
    return {
        "shop": rec["shop"], "url": rec["url"], "name": name, "price": rec.get("price"),
        "brand": brand, "brand_status": rec.get("brand_status"),
        "model": model, "network": network, "ram_gb": ram, "storage_gb": storage,
        "colour": extract_colour(name), "spec_status": status, "notes": notes,
    }


def load_records(data_dir, product_type):
    seen, out = set(), []
    for f in sorted(Path(data_dir).glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for rec in data:
            if rec.get("product_type") != product_type:
                continue
            key = (rec["shop"], rec["url"])
            if key in seen:
                continue
            seen.add(key)
            out.append(rec)
    return out


def build_report(rows):
    L = []
    add = L.append
    shops = sorted({r["shop"] for r in rows})
    add(f"Phone extraction report: {len(rows)} unique listings\n")

    add("== Spec parsing by retailer (ok = RAM and storage both found) ==")
    for s in shops:
        c = Counter(r["spec_status"] for r in rows if r["shop"] == s)
        add(f"  {s:18} total {sum(c.values()):4}  ok {c['ok']:4}  partial {c['partial']:3}  none {c['none']:3}")
    add("")

    add("== Brand status (only 'matched' listings are eligible for matching) ==")
    bc = Counter(r["brand_status"] for r in rows)
    add("  " + "  ".join(f"{k}: {v}" for k, v in sorted(bc.items(), key=lambda x: str(x[0]))))
    add("")

    add("== Other counts ==")
    add(f"  colour not found: {sum(1 for r in rows if not r['colour'])}")
    add(f"  network (4G/5G) not in name: {sum(1 for r in rows if not r['network'])}")
    nc = Counter(n for r in rows for n in r["notes"])
    add("  notes: " + (", ".join(f"{k}={v}" for k, v in nc.most_common()) or "none"))
    add("")

    problems = [r for r in rows if r["spec_status"] != "ok" or r["notes"]]
    add(f"== Listings needing a look ({len(problems)}) ==")
    for r in problems:
        add(f"  [{r['shop']}] {r['name']}")
        add(f"      -> model='{r['model']}' ram={r['ram_gb']} storage={r['storage_gb']} "
            f"status={r['spec_status']} notes={r['notes']}")
    add("")

    eligible = [r for r in rows if r["brand_status"] == "matched"
                and r["spec_status"] == "ok" and r["model"]]
    groups = defaultdict(list)
    for r in eligible:
        groups[(r["brand"], r["model"], r["network"], r["ram_gb"], r["storage_gb"])].append(r)
    multi = {k: v for k, v in groups.items() if len({x["shop"] for x in v}) >= 2}
    add(f"== Exact candidate groups across 2+ retailers: {len(multi)} "
        f"(of {len(groups)} distinct keys, {len(eligible)} eligible listings) ==")
    for k, v in sorted(multi.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        add(f"  {k}")
        for x in v:
            add(f"      [{x['shop']}] {x['price']}  {x['name']}")
    add("")

    # near misses: same brand/RAM/storage, one model's tokens contained in the other's
    buckets = defaultdict(list)
    for r in eligible:
        buckets[(r["brand"], r["ram_gb"], r["storage_gb"])].append(r)
    near = []
    for key, rs in buckets.items():
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                if a["shop"] == b["shop"] or (a["model"], a["network"]) == (b["model"], b["network"]):
                    continue
                ta, tb = set(a["model"].split()), set(b["model"].split())
                if ta < tb or tb < ta or (ta == tb):
                    near.append((a, b))
                elif a["model"] == b["model"]:  # differs only by network
                    near.append((a, b))
    add(f"== Near misses (same brand/RAM/storage; model text nested or network differs): {len(near)} ==")
    add("   Review by hand. These must NOT be merged automatically.")
    for a, b in near:
        add(f"  [{a['shop']}] '{a['model']}' {a['network']}  <->  [{b['shop']}] '{b['model']}' {b['network']}"
            f"   ({a['brand']} {a['ram_gb']}/{a['storage_gb']})")
    add("")

    add("== Distinct model strings per brand (eyeball for parse errors) ==")
    mb = defaultdict(Counter)
    for r in rows:
        mb[r["brand"] or "(no brand)"][r["model"]] += 1
    for b, c in sorted(mb.items(), key=lambda kv: -sum(kv[1].values())):
        add(f"  {b} ({sum(c.values())} listings, {len(c)} model strings)")
        for m, n in sorted(c.items()):
            add(f"      {n:3} x {m}")
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
    rows = [parse_record(r) for r in records]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "phone_extraction.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    report = build_report(rows)
    (out / "phone_extraction_report.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {out / 'phone_extraction_report.txt'} and {out / 'phone_extraction.json'}")


if __name__ == "__main__":
    main()
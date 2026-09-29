"""Validate taxonomy.json + aliases.json. Usage:
   python validate_taxonomy.py [cleaned_data_dir]
Exits non-zero on any problem. With a cleaned_data dir, also checks that every
observed (shop, category, subcategory) has a mapping and every mapping is used."""
import json, sys, glob, pathlib
here = pathlib.Path(__file__).parent
tax = json.loads((here / "taxonomy.json").read_text(encoding="utf-8"))
ali = json.loads((here / "aliases.json").read_text(encoding="utf-8"))
NONE = ali["null_subcategory_key"]
errors, warnings = [], []
if ali["taxonomy_version"] != tax["version"]:
    errors.append("aliases.taxonomy_version != taxonomy.version")
owner = {}
for cat, types in tax["categories"].items():
    for t in types:
        if t in owner: errors.append(f"type {t!r} under both {owner[t]!r} and {cat!r}")
        owner[t] = cat
        if t in tax["categories"]: errors.append(f"type {t!r} clashes with a category name")
used_types, keys = set(), set()
for shop, cats in ali["mappings"].items():
    for cat, subs in cats.items():
        for sub, e in subs.items():
            keys.add((shop.casefold(), cat.casefold(), sub.casefold()))
            where = f"{shop}/{cat}/{sub}"
            st, t = e["status"], e.get("product_type")
            if st == "mapped":
                if t not in owner: errors.append(f"{where}: type {t!r} not in taxonomy")
                if "category" in e: errors.append(f"{where}: mapped rows must not carry a category (derived from type)")
                used_types.add(t)
            elif st == "parent_only":
                if t: errors.append(f"{where}: parent_only must have null product_type")
                if e.get("category") not in tax["categories"]: errors.append(f"{where}: unknown category {e.get('category')!r}")
            elif st == "unmapped":
                if t or e.get("category"): errors.append(f"{where}: unmapped must be empty")
            else: errors.append(f"{where}: bad status {st!r}")
for t in owner:
    if t not in used_types: warnings.append(f"taxonomy type never used by any alias: {t}")
if len(sys.argv) > 1:
    seen = {}
    for f in glob.glob(str(pathlib.Path(sys.argv[1]) / "*.json")):
        data = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        if not isinstance(data, list): continue
        for p in data:
            sub = p.get("subcategory") or NONE
            k = (str(p["shop"]).casefold(), str(p["category"]).casefold(), str(sub).casefold())
            seen[k] = seen.get(k, 0) + 1
    for k, n in sorted(seen.items()):
        if k not in keys: errors.append(f"UNMAPPED combination in data: {k} ({n} records)")
    for k in sorted(keys - set(seen)): warnings.append(f"alias key not seen in data: {k}")
for w in warnings: print("WARN ", w)
for e in errors: print("ERROR", e)
print(f"{len(errors)} errors, {len(warnings)} warnings")
sys.exit(1 if errors else 0)
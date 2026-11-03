"""Names as the site shows them.

Some stores put their own filing in front of a name, like Oxygen's
"ASUS:LAPTOPS: TUF A15 ...". The stored name keeps it (type detection and
matching read those words); only what the API sends out is tidied, to
"ASUS TUF A15 ...".
"""

import re

# BRAND:CATEGORY: at the start, both in capitals.
_FILING = re.compile(r"^\s*([A-Z0-9][A-Z0-9 .&+/'-]*?)\s*:\s*[A-Z0-9][A-Z0-9 .&+/'-]*?\s*:\s*")


def shown_name(name: str) -> str:
    match = _FILING.match(name)
    if not match:
        return name
    brand, rest = match.group(1), name[match.end():].strip()
    if not rest:
        return name
    if rest.lower().startswith(brand.lower()):
        return rest
    return f"{brand} {rest}"

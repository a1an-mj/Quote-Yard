import json
import re


INPUT_FILE = "data/myg_laptops.json"
OUTPUT_FILE = "data/myg_laptops_parsed.json"


# --------------------------------------------------
# RAM + STORAGE
# --------------------------------------------------

def extract_memory_specs(parts):
    """
    Find RAM and storage values such as:

    8 GB
    16GB
    512 GB
    1 TB
    512 GB SSD
    """

    found = []

    for part in parts:

        matches = re.findall(
            r"(?<!\w)(\d+\s*(?:GB|TB))(?!\w)",
            part,
            re.IGNORECASE
        )

        for match in matches:

            value = match.strip()

            if value not in found:
                found.append(value)

    ram = found[0] if len(found) >= 1 else None
    storage = found[1] if len(found) >= 2 else None

    return ram, storage


# --------------------------------------------------
# OPERATING SYSTEM
# --------------------------------------------------

def find_os(parts):

    for part in parts:

        if re.search(
            r"Windows|macOS|Chrome OS|Linux|Ubuntu",
            part,
            re.IGNORECASE
        ):
            return part.strip()

    return None


# --------------------------------------------------
# PROCESSOR
# --------------------------------------------------

def find_processor(product_name, url):

    sources = []

    if product_name:
        sources.append(product_name)

    if url:
        # Convert URL separators into spaces.
        normalized_url = re.sub(r"[-_/]+", " ", url)
        sources.append(normalized_url)

    # More specific processors come first.
    #
    # IMPORTANT:
    # The optional model number must NOT be a RAM value.
    #
    # Example:
    #   Intel Core i5 8 GB
    #
    # We want:
    #   Intel Core i5
    #
    # NOT:
    #   Intel Core i5 8

    processor_patterns = [

        # ------------------------------------------
        # Intel Core Ultra
        # ------------------------------------------

        r"\bIntel\s+Core\s+Ultra\s+\d+"
        r"(?:\s+\d+[A-Za-z]{1,4})?"
        r"(?!\s*(?:GB|TB)\b)",

        # ------------------------------------------
        # Intel Core i-series
        # ------------------------------------------

        r"\bIntel\s+Core\s+i[3579]"
        r"(?:\s+\d+[A-Za-z]{1,4})?"
        r"(?!\s*(?:GB|TB)\b)",

        # ------------------------------------------
        # Intel Core numbered series
        #
        # Examples:
        # Core 3
        # Core 3 100U
        # Core 5
        # Core 5 320
        # Core 7
        # ------------------------------------------

        r"\bIntel\s+Core\s+\d+"
        r"(?:\s+\d+[A-Za-z]{1,4})?"
        r"(?!\s*(?:GB|TB)\b)",

        # ------------------------------------------
        # Intel 13th Gen / 14th Gen etc.
        # ------------------------------------------

        r"\bIntel\s+\d{2}(?:st|nd|rd|th)\s+Gen\b",

        # ------------------------------------------
        # AMD Ryzen AI
        #
        # Ryzen AI 7 350
        # Ryzen AI 5 330
        # ------------------------------------------

        r"\b(?:AMD\s+)?Ryzen\s+AI\s+\d+"
        r"(?:\s+\d+[A-Za-z]{1,4})?"
        r"(?!\s*(?:GB|TB)\b)",

        # ------------------------------------------
        # AMD Ryzen R-series
        #
        # Ryzen R3 5300U
        # ------------------------------------------

        r"\b(?:AMD\s+)?Ryzen\s+R\d+"
        r"(?:\s+\d+[A-Za-z]{1,4})?"
        r"(?!\s*(?:GB|TB)\b)",

        # ------------------------------------------
        # AMD Ryzen
        #
        # Ryzen 7 7735HS
        # Ryzen 7 260
        # Ryzen 5 40
        # Ryzen 3
        # ------------------------------------------

        r"\b(?:AMD\s+)?Ryzen\s+\d+"
        r"(?:\s+\d+[A-Za-z]{1,5})?"
        r"(?!\s*(?:GB|TB)\b)",

        # ------------------------------------------
        # Apple M-series
        #
        # M5 Chip
        # M5 Pro Chip
        # M5 Pro
        # ------------------------------------------

        r"\b(?:Apple\s+)?M\d+"
        r"(?:\s+(?:Pro|Max|Ultra))?"
        r"(?:\s+[Cc]hip)?",

        # ------------------------------------------
        # Apple A-series
        #
        # A18 Pro chip
        # ------------------------------------------

        r"\b(?:Apple\s+)?A\d+"
        r"(?:\s+(?:Pro|Max|Ultra))?"
        r"(?:\s+[Cc]hip)?",
    ]


    # --------------------------------------------------
    # SEARCH PRODUCT NAME FIRST
    # --------------------------------------------------

    for source in sources[:1]:

        for pattern in processor_patterns:

            match = re.search(
                pattern,
                source,
                re.IGNORECASE
            )

            if match:
                return match.group(0).strip()


    # --------------------------------------------------
    # SEARCH URL SECOND
    # --------------------------------------------------

    if len(sources) > 1:

        url_source = sources[1]

        for pattern in processor_patterns:

            match = re.search(
                pattern,
                url_source,
                re.IGNORECASE
            )

            if match:

                processor = match.group(0).strip()

                # --------------------------------------
                # Extra protection:
                #
                # Never allow RAM/storage to sneak in.
                # --------------------------------------

                processor = re.sub(
                    r"\s+(?:\d+\s*)?(?:GB|TB)\b.*$",
                    "",
                    processor,
                    flags=re.IGNORECASE
                )

                return processor.strip()


    return None


# --------------------------------------------------
# MODEL CODE
# --------------------------------------------------

def find_model_code(parts):

    candidates = []

    for part in parts:

        part = part.strip()

        # "NW" is not the model code.
        if part.upper() == "NW":
            continue

        # Model codes generally:
        # - contain numbers
        # - have no spaces
        # - contain letters/numbers/some punctuation

        if (
            len(part) >= 6
            and " " not in part
            and re.search(r"\d", part)
            and re.fullmatch(
                r"[A-Za-z0-9./_-]+",
                part
            )
        ):
            candidates.append(part)

    if candidates:
        return candidates[-1]

    return None


# --------------------------------------------------
# PARSE PRODUCT
# --------------------------------------------------

def parse_product(product):

    raw_name = product["name"].strip()

    parts = [
        part.strip()
        for part in raw_name.split("|")
        if part.strip()
    ]

    name = parts[0]

    remaining = parts[1:]

    ram, storage = extract_memory_specs(
        remaining
    )

    os = find_os(
        remaining
    )

    processor = find_processor(
        raw_name,
        product.get("url")
    )

    model_code = find_model_code(
        remaining
    )

    return {
        "name": name,
        "processor": processor,
        "ram": ram,
        "storage": storage,
        "os": os,
        "model_code": model_code,
        "price": product["price"],
        "availability": product["availability"],
        "url": product["url"]
    }


# --------------------------------------------------
# LOAD RAW DATA
# --------------------------------------------------

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    products = json.load(file)


# --------------------------------------------------
# PARSE ALL PRODUCTS
# --------------------------------------------------

parsed_products = [
    parse_product(product)
    for product in products
]


# --------------------------------------------------
# SAVE
# --------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        parsed_products,
        file,
        indent=4,
        ensure_ascii=False
    )


print(
    f"Total products: {len(parsed_products)}"
)

print(
    f"Saved to {OUTPUT_FILE}"
)
import json

INPUT_FILE = "data/myg_tv.json"
OUTPUT_FILE = "data/myg_tv_parsed.json"


def parse_product(product):
    # Keep only the actual product name
    # Everything after the first "|" is ignored.
    raw_name = product["name"]

    name = raw_name.split("|")[0].strip()

    return {
        "name": name,
        "price": product["price"],
        "url": product["url"],
        "availability": product["availability"],
        "shop": product["shop"],
        "category": product["category"]
    }


# Read raw tv data
with open(INPUT_FILE, "r", encoding="utf-8") as file:
    products = json.load(file)


# Parse product names
parsed_products = [
    parse_product(product)
    for product in products
]


# Save parsed data
with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(
        parsed_products,
        file,
        indent=4,
        ensure_ascii=False
    )


print(f"Total products: {len(parsed_products)}")
print(f"Saved to: {OUTPUT_FILE}")
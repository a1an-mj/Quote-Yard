import json
import re


# Load the original scraped data
with open("myg_products.json", "r", encoding="utf-8") as file:
    products = json.load(file)


parsed_products = []


for product in products:

    name = product["name"]

    # Split product name into parts
    parts = [part.strip() for part in name.split("|")]

    ram = None
    storage = None
    color = None

    # --------------------------------------------------
    # Find RAM and storage
    # --------------------------------------------------

    gb_indexes = []
    gb_values = []

    for index, part in enumerate(parts):

        match = re.fullmatch(
            r"(\d+)\s*GB",
            part,
            re.IGNORECASE
        )

        if match:
            gb_indexes.append(index)
            gb_values.append(int(match.group(1)))

    # --------------------------------------------------
    # Identify RAM and storage
    # --------------------------------------------------

    if len(gb_values) >= 2:

        first = gb_values[0]
        second = gb_values[1]

        if first <= second:
            ram = f"{first} GB"
            storage = f"{second} GB"
        else:
            ram = f"{second} GB"
            storage = f"{first} GB"

        # The color normally comes immediately
        # after the second GB value.
        storage_index = gb_indexes[1]

        if storage_index + 1 < len(parts):

            possible_color = parts[storage_index + 1]

            # Don't treat obvious model codes as colors
            if possible_color.upper() not in ["NM", "NM1"]:
                color = possible_color

    # --------------------------------------------------
    # Handle phones without RAM/storage
    # --------------------------------------------------

    else:

        # Example:
        # Nokia 110 Power Keypad Phone | Dual SIM | Purple | TA-1751

        if len(parts) >= 3:

            possible_color = parts[-2]

            # Model codes usually look like TA-1751,
            # so the second-last part is treated as color.
            color = possible_color

    # --------------------------------------------------
    # Create cleaned product
    # --------------------------------------------------

    cleaned_product = {
        "name": name,
        "ram": ram,
        "storage": storage,
        "color": color,
        "price": product["price"],
        "url": product["url"],
        "availability": product["availability"]
    }

    parsed_products.append(cleaned_product)


# --------------------------------------------------
# Save parsed data
# --------------------------------------------------

with open("myg_products_parsed.json", "w", encoding="utf-8") as file:

    json.dump(
        parsed_products,
        file,
        indent=4,
        ensure_ascii=False
    )


# --------------------------------------------------
# Summary
# --------------------------------------------------

print("=" * 60)
print("PARSING COMPLETE")
print("=" * 60)

print(f"Total products: {len(parsed_products)}")
print("Saved to: myg_products_parsed.json")

print()
print("Sample results:")
print("-" * 60)

for product in parsed_products[:10]:

    print()
    print("Name:", product["name"])
    print("RAM:", product["ram"])
    print("Storage:", product["storage"])
    print("Color:", product["color"])
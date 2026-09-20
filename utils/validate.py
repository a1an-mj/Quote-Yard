import json


with open("myg_products_parsed.json", "r", encoding="utf-8") as file:
    products = json.load(file)


print("Total products:", len(products))

print()
print("Products with missing color:")
print("-" * 60)

missing_color = 0

for product in products:

    if product["color"] is None:
        print(product["name"])
        missing_color += 1


print()
print("Products with missing RAM:")
print("-" * 60)

missing_ram = 0

for product in products:

    if product["ram"] is None:
        print(product["name"])
        missing_ram += 1


print()
print("=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)

print("Total:", len(products))
print("Missing color:", missing_color)
print("Missing RAM:", missing_ram)

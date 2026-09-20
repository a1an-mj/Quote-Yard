import json

with open("myg_products.json", "r", encoding="utf-8") as file:
    products = json.load(file)

print("Total products:", len(products))

print("\nFirst 10 products:")
for product in products[:10]:
    print(product)

print("\nMissing prices:")
for product in products:
    if product["price"] is None:
        print(product["name"])

print("\nMissing availability:")
for product in products:
    if product["availability"] is None:
        print(product["name"])
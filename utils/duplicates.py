import json
from collections import Counter


with open("myg_products.json", "r", encoding="utf-8") as file:
    products = json.load(file)


# Check duplicate names
name_counts = Counter(product["name"] for product in products)

print("Duplicate product names:")
print("-" * 50)

for name, count in name_counts.items():
    if count > 1:
        print(f"{count}x  {name}")


# Check duplicate URLs
url_counts = Counter(product["url"] for product in products)

print("\nDuplicate URLs:")
print("-" * 50)

for url, count in url_counts.items():
    if count > 1:
        print(f"{count}x  {url}")
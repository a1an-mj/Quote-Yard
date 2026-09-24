from playwright.sync_api import sync_playwright
import json

BASE_URL = "https://www.myg.in/tablets/"


def clean_price(price_text):
    if not price_text:
        return None

    price_text = price_text.replace(",", "").strip()

    try:
        return int(float(price_text))
    except ValueError:
        return None


def scrape_page(page):
    page.wait_for_timeout(3000)

    products = page.locator("a.line-clamp-2")

    print(f"Products found: {products.count()}")

    page_products = []

    for product in products.all():
        name = product.inner_text().strip()
        url = product.get_attribute("href")

        parent = product.locator("..")

        # Price
        price_element = parent.locator(
            '[id^="sec_discounted_price_"]'
        )

        if price_element.count() > 0:
            price = clean_price(
                price_element.inner_text().strip()
            )
        else:
            price = None

        # Availability
        availability_element = parent.locator("p.text-green")

        if availability_element.count() > 0:
            availability = availability_element.inner_text().strip()
        else:
            availability = None

        page_products.append({
            "name": name,
            "price": price,
            "url": url,
            "availability": availability,
            "shop": "myG",
            "category": "Tablets"
        })

    return page_products


with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    all_products = []
    page_number = 1

    while True:

        if page_number == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}page-{page_number}/"

        print()
        print("=" * 60)
        print(f"SCRAPING TABLETS - PAGE {page_number}")
        print(url)
        print("=" * 60)

        page.goto(url, wait_until="domcontentloaded")

        products = scrape_page(page)

        if not products:
            print("No products found. Stopping.")
            break

        all_products.extend(products)

        print(f"Products collected so far: {len(all_products)}")

        page_number += 1

    with open(
        "data/myg_tablets.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_products,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()
    print("=" * 60)
    print("TABLET SCRAPING COMPLETE")
    print("=" * 60)

    print(f"Total products: {len(all_products)}")
    print("Saved to: data/myg_tablets.json")

    browser.close()
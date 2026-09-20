from playwright.sync_api import sync_playwright

URL = "https://www.myg.in/laptop-desktops/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(URL)
    page.wait_for_timeout(3000)

    products = page.locator("a.line-clamp-2")

    for product in products.all():
        name = product.inner_text().strip()

        parent = product.locator("..")

        price_element = parent.locator('[id^="sec_discounted_price_"]')

        if price_element.count() > 0:
            price = price_element.inner_text().strip()
        else:
            price = None

        availability_element = parent.locator("p.text-green")

        if availability_element.count() > 0:
            availability = availability_element.inner_text().strip()
        else:
            availability = None

        print()
        print("Name:", name)
        print("Price:", price)
        print("Availability:", availability)

    browser.close()
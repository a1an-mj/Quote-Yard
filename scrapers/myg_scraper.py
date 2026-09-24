"""
MyG.in product scraper — goes through every category in CATEGORIES
one after another, in a single browser session, writing one JSON
file per category.

Usage:
    python myg_scraper.py                          # scrape every category
    python myg_scraper.py --headless
    python myg_scraper.py --only mobiles tablets    # scrape a subset
    python myg_scraper.py --max-pages 20
"""

import argparse
import json
import logging
import re
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("myg_scraper")

# ---------------------------------------------------------------------------
# Category configuration — add new categories here instead of copy-pasting
# a whole new script.
# ---------------------------------------------------------------------------
CATEGORIES = {
    "mobiles": {
        "base_url": "https://www.myg.in/mobile-phones/",
        "output": "data/myg_mobile.json",
        "label": "Mobiles",
    },
    "laptops": {
        "base_url": "https://www.myg.in/laptop-desktops/",
        "output": "data/myg_laptops.json",
        "label": "Laptops",
    },
    "tablets": {
        "base_url": "https://www.myg.in/tablets/",
        "output": "data/myg_tablets.json",
        "label": "Tablets",
    },
    "accessories": {
        "base_url": "https://www.myg.in/accessories/",
        "output": "data/myg_accessories.json",
        "label": "Accessories",
    },
    "home-kitchen": {
        "base_url": "https://www.myg.in/home-and-kitchen/",
        "output": "data/myg_home_kitchen.json",
        "label": "Home & Kitchen",
    },
    "refrigerators": {
        "base_url": "https://www.myg.in/refrigerators/",
        "output": "data/myg_refrigerators.json",
        "label": "Refrigerators",
    },
    "washing-machines": {
        "base_url": "https://www.myg.in/washing-machines/",
        "output": "data/myg_washing_machines.json",
        "label": "Washing Machines",
    },
    "air-conditioners": {
        "base_url": "https://www.myg.in/air-conditioners-en/",
        "output": "data/myg_air_conditioners.json",
        "label": "Air Conditioners",
    },
    "small-appliances": {
        "base_url": "https://www.myg.in/small-appliances/",
        "output": "data/myg_small_appliances.json",
        "label": "Small Appliances",
    },
    "personal-care": {
        "base_url": "https://www.myg.in/personal-care/",
        "output": "data/myg_personal_care.json",
        "label": "Personal Care",
    },
    "home-automation": {
        "base_url": "https://www.myg.in/home-automation/",
        "output": "data/myg_home_automation.json",
        "label": "Home Automation",
    },
}

PRODUCT_LINK_SELECTOR = "a.line-clamp-2"
PRICE_SELECTOR = '[id^="sec_discounted_price_"]'
AVAILABILITY_SELECTOR = "p.text-green"

SAFETY_MAX_PAGES = 100  # hard stop so a bug can never spin forever

# Resource types we don't need for the JSON output. Blocking them keeps
# Chromium much lighter over a long scraping session.
BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}


def block_heavy_resources(route):
    """Abort requests for resources we don't need for the JSON output."""
    if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
        route.abort()
    else:
        route.continue_()


def clean_price(price_text: str | None) -> int | None:
    """Turn '₹1,23,456.00' style text into an int, or None if unparseable."""
    if not price_text:
        return None

    # Strip anything that isn't a digit or a decimal point (commas, ₹, spaces, etc.)
    numeric = re.sub(r"[^\d.]", "", price_text)
    if not numeric:
        return None

    try:
        return int(float(numeric))
    except ValueError:
        return None


def scrape_page(page: Page, shop_name: str = "myG", category_label: str | None = None) -> list[dict]:
    """Scrape one listing page that is already loaded into `page`."""
    page.wait_for_selector(PRODUCT_LINK_SELECTOR, timeout=10_000)

    products = page.locator(PRODUCT_LINK_SELECTOR)
    count = products.count()
    log.info("Products found on page: %d", count)

    page_products = []

    for product in products.all():
        name = product.inner_text().strip()
        url = product.get_attribute("href")
        parent = product.locator("..")

        price_element = parent.locator(PRICE_SELECTOR)
        price = clean_price(price_element.inner_text().strip()) if price_element.count() > 0 else None

        availability_element = parent.locator(AVAILABILITY_SELECTOR)
        availability = (
            availability_element.inner_text().strip() if availability_element.count() > 0 else None
        )

        page_products.append(
            {
                "name": name,
                "price": price,
                "url": url,
                "availability": availability,
                "shop": shop_name,
                "category": category_label,
            }
        )

    return page_products


def scrape_category(
    page: Page,
    base_url: str,
    max_pages: int = SAFETY_MAX_PAGES,
    category_label: str | None = None,
) -> list[dict]:
    """Scrape every page of one category using an already-open `page`.
    Does NOT launch or close a browser — that happens once in main()
    and is reused across all categories."""
    all_products: list[dict] = []
    page_number = 1

    while page_number <= max_pages:
        url = base_url if page_number == 1 else f"{base_url}page-{page_number}/"

        log.info("=" * 60)
        log.info("SCRAPING %s - PAGE %d: %s", category_label or "PRODUCTS", page_number, url)

        response = page.goto(url, wait_until="domcontentloaded")

        # Stop this category cleanly if MyG returns 403.
        if response and response.status == 403:
            log.warning("MyG returned 403 Forbidden. Stopping category.")
            break

        products = scrape_page(page, category_label=category_label)

        if not products:
            log.info("No products found. Stopping category.")
            break

        all_products.extend(products)
        log.info("Products collected so far: %d", len(all_products))
        page_number += 1
    else:
        log.warning("Hit SAFETY_MAX_PAGES (%d) without an empty page — stopped early.", max_pages)

    return all_products


def save_products(products: list[dict], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(products, indent=4, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape MyG.in. With no arguments, scrapes every category in CATEGORIES, one after another."
    )
    parser.add_argument("--headless", action="store_true", help="Run browser headless")
    parser.add_argument("--max-pages", type=int, default=SAFETY_MAX_PAGES, help="Safety cap on page count")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=CATEGORIES.keys(),
        default=None,
        help="Restrict the run to specific category keys (default: run all)",
    )
    args = parser.parse_args()

    categories_to_run = args.only if args.only else list(CATEGORIES.keys())
    summary: dict[str, int] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        # Routes registered on the context apply to every page opened from it.
        context = browser.new_context()
        context.route("**/*", block_heavy_resources)
        try:
            for key in categories_to_run:
                config = CATEGORIES[key]
                log.info("#" * 60)
                log.info("STARTING CATEGORY: %s", config["label"])
                log.info("#" * 60)

                # Fresh page per category so memory from one category
                # doesn't carry over into the next.
                page = context.new_page()
                try:
                    products = scrape_category(
                        page,
                        config["base_url"],
                        max_pages=args.max_pages,
                        category_label=config["label"],
                    )
                finally:
                    page.close()

                save_products(products, config["output"])
                summary[config["label"]] = len(products)

                log.info("Saved %d products to %s", len(products), config["output"])
        finally:
            browser.close()

    log.info("=" * 60)
    log.info("ALL CATEGORIES COMPLETE")
    for label, count in summary.items():
        log.info("  %-25s %d products", label, count)
    log.info("Total: %d products across %d categories", sum(summary.values()), len(summary))


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Quote Yard - Oxygen Digital Shop scraper

Scrapes Oxygen collection/listing pages.

Current fields:
    name
    price
    url
    availability
    shop
    category

The scraper does NOT parse RAM/storage/etc. from product names and does
NOT visit product-detail pages yet.

Usage:
    python scrapers/oxygen_scraper.py
    python scrapers/oxygen_scraper.py --headless
    python scrapers/oxygen_scraper.py --only mobiles laptops
    python scrapers/oxygen_scraper.py --only laptops --max-pages 1
"""

import argparse
import json
import logging
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


BASE_URL = "https://www.oxygendigitalshop.com"

CATEGORIES = {
    "mobiles": {
        "base_url": f"{BASE_URL}/collections/mobile-smart-phones",
        "output": "data/oxygen_mobiles.json",
        "label": "Mobiles",
    },
    "laptops": {
        "base_url": f"{BASE_URL}/collections/laptops",
        "output": "data/oxygen_laptops.json",
        "label": "Laptops",
    },
    "kitchen-appliances": {
        "base_url": f"{BASE_URL}/collections/kitchen-appliances",
        "output": "data/oxygen_kitchen_appliances.json",
        "label": "Kitchen Appliances",
    },
    "refrigerators": {
        "base_url": f"{BASE_URL}/collections/refrigerators",
        "output": "data/oxygen_refrigerators.json",
        "label": "Refrigerators",
    },
    "washing-machines": {
        "base_url": f"{BASE_URL}/collections/washing-machines",
        "output": "data/oxygen_washing_machines.json",
        "label": "Washing Machines",
    },
    "inverter": {
        "base_url": f"{BASE_URL}/collections/inverter",
        "output": "data/oxygen_inverter.json",
        "label": "Inverter",
    },
    "battery": {
        "base_url": f"{BASE_URL}/collections/battery",
        "output": "data/oxygen_battery.json",
        "label": "Battery",
    },
    "gadgets": {
        "base_url": f"{BASE_URL}/collections/gadgets",
        "output": "data/oxygen_gadgets.json",
        "label": "Gadgets",
    },
    "monitors": {
        "base_url": f"{BASE_URL}/collections/monitors",
        "output": "data/oxygen_monitors.json",
        "label": "Monitors",
    },
    "printers": {
        "base_url": f"{BASE_URL}/collections/printers",
        "output": "data/oxygen_printers.json",
        "label": "Printers",
    },
    "led-tv": {
        "base_url": f"{BASE_URL}/collections/led-tv",
        "output": "data/oxygen_led_tv.json",
        "label": "LED TV",
    },
}

PRODUCT_CARD_SELECTOR = "div.custom-product-card"
PRODUCT_TITLE_ATTRIBUTE = "data-product-title"
PRODUCT_PRICE_ATTRIBUTE = "data-product-price"
PRODUCT_URL_ATTRIBUTE = "data-product-url"

BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}

DEFAULT_MAX_PAGES = 100
DEFAULT_WAIT_MS = 500
DEFAULT_NAV_TIMEOUT = 30_000


def clean_price(raw_price: str | None) -> int | None:
    """
    Convert Oxygen's product-card price to rupees.

    Oxygen exposes values such as:
        1349900 -> ₹13,499

    Therefore the card value is treated as paise.
    """
    if not raw_price:
        return None

    cleaned = re.sub(r"[^\d.]", "", raw_price)

    if not cleaned:
        return None

    try:
        value = float(cleaned)
    except ValueError:
        return None

    return int(round(value / 100))


def detect_availability(card) -> str | None:
    """
    Determine availability from the product card.

    Oxygen's cards use purchase-state text such as:
        ADD TO CART
        SOLD OUT
        OUT OF STOCK
    """

    try:
        text = " ".join(card.inner_text(timeout=2_000).split()).lower()

        if "out of stock" in text or "sold out" in text:
            return "Out of stock"

        if "add to cart" in text:
            return "In stock"

        # Fallback: inspect buttons/links inside the card.
        controls = card.locator("button, a")

        for index in range(controls.count()):
            control_text = (
                controls.nth(index)
                .inner_text(timeout=1_000)
                .strip()
                .lower()
            )

            if "out of stock" in control_text or "sold out" in control_text:
                return "Out of stock"

            if "add to cart" in control_text:
                return "In stock"

    except Exception:
        pass

    return None


def build_page_url(base_url: str, page_number: int) -> str:
    """
    Oxygen uses Shopify-style collection pagination.
    """
    if page_number == 1:
        return base_url

    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page_number}"


def block_resources(route):
    if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
        route.abort()
    else:
        route.continue_()


def scrape_page(
    page: Page,
    url: str,
    category: str,
) -> tuple[list[dict], int]:
    """
    Scrape one Oxygen collection page.

    Returns:
        products, HTTP status
    """

    logging.info("Opening %s", url)

    response = page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=DEFAULT_NAV_TIMEOUT,
    )

    status = response.status if response else 0

    if status == 404:
        logging.warning("Page does not exist (404). Stopping category.")
        return [], 404

    if status == 403:
        logging.warning("Oxygen returned 403 Forbidden. Stopping category.")
        return [], 403

    if status >= 500:
        logging.warning("Oxygen returned HTTP %s.", status)
        return [], status

    try:
        page.wait_for_selector(
            PRODUCT_CARD_SELECTOR,
            state="attached",
            timeout=10_000,
        )
    except PlaywrightTimeoutError:
        logging.warning("No product cards found on %s.", url)
        return [], status

    cards = page.locator(PRODUCT_CARD_SELECTOR)
    count = cards.count()

    products = []

    for index in range(count):
        card = cards.nth(index)

        name = card.get_attribute(PRODUCT_TITLE_ATTRIBUTE)
        raw_price = card.get_attribute(PRODUCT_PRICE_ATTRIBUTE)
        relative_url = card.get_attribute(PRODUCT_URL_ATTRIBUTE)

        if not name or not relative_url:
            logging.warning(
                "Skipping card %d: missing name or URL.",
                index + 1,
            )
            continue

        product_url = urljoin(BASE_URL, relative_url)

        products.append(
            {
                "name": name.strip(),
                "price": clean_price(raw_price),
                "url": product_url,
                "availability": detect_availability(card),
                "shop": "Oxygen",
                "category": category,
            }
        )

    return products, status


def scrape_category(
    context: BrowserContext,
    category_key: str,
    config: dict,
    max_pages: int,
) -> list[dict]:

    page = context.new_page()
    page.route("**/*", block_resources)

    all_products = []
    seen_urls = set()

    try:
        for page_number in range(1, max_pages + 1):

            url = build_page_url(
                config["base_url"],
                page_number,
            )

            try:
                products, status = scrape_page(
                    page,
                    url,
                    config["label"],
                )

            except Exception as exc:
                logging.exception(
                    "Failed on %s page %d: %s",
                    category_key,
                    page_number,
                    exc,
                )
                break

            if status in {403, 404}:
                break

            if not products:
                logging.info(
                    "No products found. Stopping %s at page %d.",
                    category_key,
                    page_number,
                )
                break

            new_count = 0

            for product in products:
                if product["url"] not in seen_urls:
                    seen_urls.add(product["url"])
                    all_products.append(product)
                    new_count += 1

            logging.info(
                "%s page %d: %d products (%d new)",
                category_key,
                page_number,
                len(products),
                new_count,
            )

            # Protect against a site returning the same page repeatedly.
            if new_count == 0:
                logging.info(
                    "No new product URLs found. Stopping %s.",
                    category_key,
                )
                break

            page.wait_for_timeout(DEFAULT_WAIT_MS)

    finally:
        page.close()

    return all_products


def save_json(
    products: list[dict],
    output_path: str,
) -> None:

    path = Path(output_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            products,
            file,
            ensure_ascii=False,
            indent=2,
        )

    logging.info(
        "Saved %d products to %s",
        len(products),
        path,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape Oxygen Digital Shop."
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chromium without a visible window.",
    )

    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(CATEGORIES.keys()),
        help="Scrape only selected categories.",
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum pages per category (default: {DEFAULT_MAX_PAGES}).",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    selected_categories = (
        args.only
        if args.only
        else list(CATEGORIES.keys())
    )

    with sync_playwright() as playwright:

        browser: Browser = playwright.chromium.launch(
            headless=args.headless
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 900,
            }
        )

        try:
            for category_key in selected_categories:

                config = CATEGORIES[category_key]

                logging.info(
                    "Starting category: %s",
                    category_key,
                )

                products = scrape_category(
                    context,
                    category_key,
                    config,
                    args.max_pages,
                )

                save_json(
                    products,
                    config["output"],
                )

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()

import argparse
import json
import logging
import re
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://nandilathgmart.com"

OUTPUT_DIR = Path("data")

SHOP_NAME = "Nandilath G Mart"

SAFETY_MAX_PAGES = 100

PRODUCT_CARD_SELECTOR = ".wd-product"
PRODUCT_NAME_SELECTOR = ".wd-entities-title a"

CURRENT_PRICE_SELECTOR = (
    ".price ins .woocommerce-Price-amount.amount bdi"
)

NORMAL_PRICE_SELECTOR = (
    ".price .woocommerce-Price-amount.amount bdi"
)

ADD_TO_CART_SELECTOR = ".add-to-cart-loop"


BLOCKED_RESOURCE_TYPES = {
    "image",
    "media",
    "font",
}


# ============================================================
# CATEGORY CONFIGURATION
# ============================================================

CATEGORIES = {

    "air-conditioners": {
        "label": "Air Conditioners",
        "output": "nandilath_air_conditioners.json",
        "subcategories": {
            "air-coolers": {
                "label": "Air Coolers",
                "url": f"{BASE_URL}/product-category/air-conditioner/air-coolers/",
            },
            "inverter-ac": {
                "label": "Inverter AC",
                "url": f"{BASE_URL}/product-category/air-conditioner/inverter-ac/",
            },
        },
    },

    "refrigerators": {
        "label": "Refrigerators",
        "output": "nandilath_refrigerators.json",
        "subcategories": {
            "multi-door": {
                "label": "Multi Door",
                "url": f"{BASE_URL}/product-category/refrigerators/multi-door/",
            },
            "side-by-side": {
                "label": "Side by side",
                "url": f"{BASE_URL}/product-category/refrigerators/side-by-side/",
            },
            "single-door": {
                "label": "Single Door",
                "url": f"{BASE_URL}/product-category/refrigerators/single-door/",
            },
            "commercial-refrigerators": {
                "label": "Commercial Refrigerators",
                "url": f"{BASE_URL}/product-category/refrigerators/commercial-refrigerators/",
            },
        },
    },

    "tvs": {
        "label": "LED TV",
        "output": "nandilath_tvs.json",
        "subcategories": {
            "smart-tv": {
                "label": "Smart LED TV",
                "url": f"{BASE_URL}/product-category/tvs/smart-tv/",
            },
            "led": {
                "label": "Non-Smart LED TV",
                "url": f"{BASE_URL}/product-category/tvs/led/",
            },
        },
    },

    "home-audio": {
        "label": "Home Audio",
        "output": "nandilath_home_audio.json",
        "subcategories": {
            "home-theater": {
                "label": "Home Theater",
                "url": f"{BASE_URL}/product-category/home-audio/home-theater/",
            },
            "sound-bars": {
                "label": "Sound Bars",
                "url": f"{BASE_URL}/product-category/home-audio/sound-bars/",
            },
            "speakers": {
                "label": "Speakers",
                "url": f"{BASE_URL}/product-category/home-audio/speakers/",
            },
        },
    },

    "washing-machines": {
        "label": "Washing Machines",
        "output": "nandilath_washing_machines.json",
        "subcategories": {
            "front-loading": {
                "label": "Front loading",
                "url": f"{BASE_URL}/product-category/washing-machine/front-loading/",
            },
            "top-loading": {
                "label": "Top loading",
                "url": f"{BASE_URL}/product-category/washing-machine/top-loading/",
            },
            "semi-automatic": {
                "label": "Semi Automatic",
                "url": f"{BASE_URL}/product-category/washing-machine/semi-automatic/",
            },
            "washer-dryer": {
                "label": "Washer Dryer",
                "url": f"{BASE_URL}/product-category/washing-machine/washer-dryer/",
            },
            "clothes-dryer": {
                "label": "Clothes Dryer",
                "url": f"{BASE_URL}/product-category/washing-machine/clothes-dryer/",
            },
        },
    },

    "home-appliances": {
        "label": "Home Appliances",
        "output": "nandilath_home_appliances.json",
        "subcategories": {
            "water-purifier": {
                "label": "Water Purifiers",
                "url": f"{BASE_URL}/product-category/home-appliances/water-purifier/",
            },
            "water-heaters": {
                "label": "Water Heaters",
                "url": f"{BASE_URL}/product-category/home-appliances/water-heaters/",
            },
            "vacuum-cleaner": {
                "label": "Vacuum Cleaner",
                "url": f"{BASE_URL}/product-category/home-appliances/_vacuumcleaner/",
            },
            "battery": {
                "label": "Battery",
                "url": f"{BASE_URL}/product-category/home-appliances/battery/",
            },
            "inverters": {
                "label": "Inverters",
                "url": f"{BASE_URL}/product-category/home-appliances/inverters/",
            },
            "stabilizer": {
                "label": "Stabilizer",
                "url": f"{BASE_URL}/product-category/home-appliances/stabilizer/",
            },
        },
    },

    "fans": {
        "label": "Fan",
        "output": "nandilath_fans.json",
        "subcategories": {
            "ceiling-fan": {
                "label": "Ceiling Fan",
                "url": f"{BASE_URL}/product-category/fans/ceiling-fan/",
            },
            "pedestal-fan": {
                "label": "Pedestal Fan",
                "url": f"{BASE_URL}/product-category/fans/pedestal-fan/",
            },
            "table-fan": {
                "label": "Table Fan",
                "url": f"{BASE_URL}/product-category/fans/table-fan/",
            },
            "wall-fan": {
                "label": "Wall Fan",
                "url": f"{BASE_URL}/product-category/fans/wall-fan/",
            },
        },
    },

    "kitchen-appliances": {
        "label": "Kitchen Appliances",
        "output": "nandilath_kitchen_appliances.json",
        "subcategories": {
            "dish-washer": {
                "label": "Dishwasher",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/dish-washer/",
            },
            "mixers-and-grinders": {
                "label": "Mixer Grinders",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/mixers-and-grinders/",
            },
            "wet-grinders": {
                "label": "Wet Grinders",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/wet-grinders/",
            },
            "air-fryer": {
                "label": "Air Fryer",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/air-fryer/",
            },
            "microwave-oven": {
                "label": "Microwave Oven",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/microwave-oven/",
            },
            "gas-stove": {
                "label": "Gas stove",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/gas-stove/",
            },
            "chimney": {
                "label": "Chimney",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/chimney/",
            },
            "cook-hob": {
                "label": "Cook Hob",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/cook-hob/",
            },
            "cooktop": {
                "label": "Cooktop",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/cooktop/",
            },
            "induction-cooker": {
                "label": "Induction cooker",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/induction-cooker/",
            },
            "blender-and-juicers": {
                "label": "Blender and Juicers",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/blender-and-juicers/",
            },
            "cookware": {
                "label": "Cookware",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/cookware/",
            },
            "crockery": {
                "label": "Crockery",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/crockery/",
            },
            "kettle": {
                "label": "Kettle",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/kettle/",
            },
            "sandwich-maker": {
                "label": "Sandwich Maker",
                "url": f"{BASE_URL}/product-category/sandwich-_maker/",
            },
            "soda-maker": {
                "label": "Soda Maker",
                "url": f"{BASE_URL}/product-category/kitchen-appliances/soda-maker/",
            },
        },
    },

    "laptop": {
        "label": "Laptop",
        "output": "nandilath_laptop.json",
        "subcategories": {
            "laptop": {
                "label": "Laptop",
                "url": f"{BASE_URL}/product-category/laptop_/",
            },
        },
    },

    "mobiles-laptops": {
        "label": "Mobiles & Laptops",
        "output": "nandilath_mobiles_laptops.json",
        "subcategories": {
            "smart-phones": {
                "label": "Smart Phones",
                "url": f"{BASE_URL}/product-category/mobiles-and-accessories/smartphones/",
            },
            "basic-phones": {
                "label": "Basic Phones",
                "url": f"{BASE_URL}/product-category/mobiles-and-accessories/basic-phones/",
            },
            "accessories": {
                "label": "Accessories",
                "url": f"{BASE_URL}/product-category/mobiles-and-accessories/accessories/",
            },
        },
    },

    "printer": {
        "label": "Printer",
        "output": "nandilath_printer.json",
        "subcategories": {
            "printer": {
                "label": "Printer",
                "url": f"{BASE_URL}/product-category/printer/",
            },
        },
    },
}


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

log = logging.getLogger("nandilath")


# ============================================================
# PRICE CLEANING
# ============================================================

def clean_price(price_text: str) -> Optional[int]:
    """
    Convert values such as:

        ₹42,999.00
        ₹ 42,999
        42999.00

    into:

        42999

    Returns None for invalid values.
    """

    if not price_text:
        return None

    cleaned = re.sub(r"[^\d.]", "", price_text)

    if not cleaned:
        return None

    try:
        return int(float(cleaned))
    except ValueError:
        return None


# ============================================================
# AVAILABILITY
# ============================================================

def detect_availability(card) -> str:
    """
    Nandilath uses WooCommerce.

    Normal purchasable products expose:
        .add-to-cart-loop

    WooCommerce may also mark unavailable products with:
        outofstock

    If neither gives us a clear answer, return Unknown.
    """

    try:
        card_class = card.get_attribute("class") or ""

        if "outofstock" in card_class.lower():
            return "Out of stock"

        add_to_cart = card.locator(ADD_TO_CART_SELECTOR)

        if add_to_cart.count() > 0:
            return "In stock"

    except Exception as exc:
        log.debug("Availability detection failed: %s", exc)

    return "Unknown"


# ============================================================
# PRODUCT EXTRACTION
# ============================================================

def extract_product(card, category: str, subcategory: str) -> Optional[dict]:
    """
    Extract the common Quote Yard product model.
    """

    try:
        name_link = card.locator(PRODUCT_NAME_SELECTOR).first

        if name_link.count() == 0:
            return None

        name = (name_link.inner_text() or "").strip()
        url = name_link.get_attribute("href")

        if not name or not url:
            return None

        # ----------------------------------------------------
        # Price
        # ----------------------------------------------------

        current_price_locator = card.locator(
            CURRENT_PRICE_SELECTOR
        ).first

        if current_price_locator.count() > 0:
            price_text = current_price_locator.inner_text()
        else:
            normal_price_locator = card.locator(
                NORMAL_PRICE_SELECTOR
            ).first

            if normal_price_locator.count() == 0:
                price_text = ""
            else:
                price_text = normal_price_locator.inner_text()

        price = clean_price(price_text)

        # ----------------------------------------------------
        # Availability
        # ----------------------------------------------------

        availability = detect_availability(card)

        return {
            "name": name,
            "price": price,
            "url": url,
            "availability": availability,
            "shop": SHOP_NAME,
            "category": category,
            "subcategory": subcategory,
        }

    except Exception as exc:
        log.warning("Failed to extract product: %s", exc)
        return None


# ============================================================
# SINGLE PAGE
# ============================================================

def scrape_page(
    page,
    url: str,
    category: str,
    subcategory: str,
) -> list[dict]:

    log.info("Opening: %s", url)

    try:
        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

    except Exception as exc:
        log.error("Navigation failed: %s", exc)
        return []

    # --------------------------------------------------------
    # HTTP status handling
    # --------------------------------------------------------

    if response:

        status = response.status

        if status == 403:
            log.warning("Nandilath returned 403. Stopping category.")
            return []

        if status == 404:
            log.warning("Page does not exist (404). Stopping category.")
            return []

        if status >= 500:
            log.warning(
                "Nandilath returned HTTP %s. Stopping category.",
                status,
            )
            return []

    # --------------------------------------------------------
    # Product cards
    # --------------------------------------------------------

    try:
        page.wait_for_selector(
            PRODUCT_CARD_SELECTOR,
            timeout=15000,
        )

    except PlaywrightTimeoutError:
        log.warning(
            "No product cards found on page. Stopping category."
        )
        return []

    cards = page.locator(PRODUCT_CARD_SELECTOR)

    count = cards.count()

    if count == 0:
        log.info("No products found.")
        return []

    log.info("Found %d product cards.", count)

    products = []

    for index in range(count):

        product = extract_product(
            cards.nth(index),
            category,
            subcategory,
        )

        if product:
            products.append(product)

    return products


# ============================================================
# CATEGORY SCRAPER
# ============================================================

def scrape_subcategory(
    browser,
    category: str,
    subcategory: str,
    config: dict,
    max_pages: int,
) -> list[dict]:

    base_url = config["url"]

    log.info(
        "=================================================="
    )
    log.info(
        "Category: %s | Subcategory: %s",
        category,
        subcategory,
    )
    log.info(
        "Base URL: %s",
        base_url,
    )

    # --------------------------------------------------------
    # Fresh context per subcategory
    # --------------------------------------------------------

    context = browser.new_context(
        viewport={
            "width": 1440,
            "height": 900,
        }
    )

    # --------------------------------------------------------
    # Block unnecessary resources
    # --------------------------------------------------------

    def block_resources(route):
        if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
            route.abort()
        else:
            route.continue_()

    context.route("**/*", block_resources)

    page = context.new_page()

    products = []
    seen_urls = set()

    try:

        for page_number in range(1, max_pages + 1):

            if page_number == 1:
                page_url = base_url.rstrip("/") + "/"
            else:
                page_url = (
                    base_url.rstrip("/")
                    + f"/page/{page_number}/"
                )

            page_products = scrape_page(
                page,
                page_url,
                category,
                subcategory,
            )

            if not page_products:
                break

            new_products = 0

            for product in page_products:

                product_url = product["url"]

                if product_url in seen_urls:
                    continue

                seen_urls.add(product_url)
                products.append(product)
                new_products += 1

            log.info(
                "Page %d: %d products, %d new.",
                page_number,
                len(page_products),
                new_products,
            )

            # ------------------------------------------------
            # Protect against repeated pages
            # ------------------------------------------------

            if new_products == 0:
                log.info(
                    "No new product URLs found. "
                    "Stopping category."
                )
                break

            # Small delay between pages
            page.wait_for_timeout(500)

    finally:
        page.close()
        context.close()

    log.info(
        "Finished %s / %s → %d products",
        category,
        subcategory,
        len(products),
    )

    return products


# ============================================================
# CATEGORY GROUP
# ============================================================

def scrape_category(
    browser,
    category_key: str,
    category_config: dict,
    selected_subcategories: Optional[list[str]],
    max_pages: int,
) -> list[dict]:

    category_label = category_config["label"]

    all_products = []

    subcategories = category_config["subcategories"]

    if selected_subcategories:
        subcategories = {
            key: value
            for key, value in subcategories.items()
            if key in selected_subcategories
        }

    for subcategory_key, subcategory_config in subcategories.items():

        products = scrape_subcategory(
            browser=browser,
            category=category_label,
            subcategory=subcategory_config["label"],
            config=subcategory_config,
            max_pages=max_pages,
        )

        all_products.extend(products)

    return all_products


# ============================================================
# JSON SAVING
# ============================================================

def save_json(filename: str, products: list[dict]):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIR / filename

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            products,
            file,
            indent=2,
            ensure_ascii=False,
        )

    log.info(
        "Saved %d products → %s",
        len(products),
        output_path,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="Nandilath G Mart scraper"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chromium in headless mode",
    )

    parser.add_argument(
        "--only",
        nargs="+",
        help="Scrape only selected main categories",
    )

    parser.add_argument(
        "--subcategories",
        nargs="+",
        help=(
            "Scrape selected subcategories inside "
            "the categories selected by --only"
        ),
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=SAFETY_MAX_PAGES,
        help="Maximum pages per subcategory",
    )

    args = parser.parse_args()

    selected_categories = CATEGORIES

    if args.only:

        selected_categories = {
            key: value
            for key, value in CATEGORIES.items()
            if key in args.only
        }

        unknown = set(args.only) - set(CATEGORIES)

        if unknown:
            log.warning(
                "Unknown categories: %s",
                ", ".join(sorted(unknown)),
            )

    if not selected_categories:
        log.error("No valid categories selected.")
        return

    log.info("Starting Nandilath G Mart scraper")
    log.info(
        "Categories: %s",
        ", ".join(selected_categories.keys()),
    )

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=args.headless
        )

        try:

            for category_key, category_config in selected_categories.items():

                products = scrape_category(
                    browser=browser,
                    category_key=category_key,
                    category_config=category_config,
                    selected_subcategories=args.subcategories,
                    max_pages=args.max_pages,
                )

                save_json(
                    category_config["output"],
                    products,
                )

        finally:
            browser.close()

    log.info("Nandilath scraping complete.")


if __name__ == "__main__":
    main()
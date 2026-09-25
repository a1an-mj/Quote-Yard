# scrapers/pittappillil_scraper.py

import argparse
import json
import logging
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


# ============================================================
# CONFIG
# ============================================================

BASE_URL = "https://www.pittappillilonline.com"

SHOP_NAME = "Pittappillil"

DATA_DIR = Path("data")

SAFETY_MAX_PAGES = 100
PAGE_LIMIT = 12
PAGE_DELAY_MS = 500


# ============================================================
# CATEGORIES
#
# Two levels:
#   - a main category (what we group into one JSON file)
#   - subcategories within it (what we actually scrape/paginate)
#
# Every scraped product keeps BOTH "category" (main) and
# "subcategory" (specific) fields. This matches how the data
# will eventually live in PostgreSQL: one category with many
# subcategories underneath it.
# ============================================================

CATEGORIES = {

    # --------------------------------------------------------
    # Kitchen Appliances
    # --------------------------------------------------------

    "kitchen-appliances": {
        "label": "Kitchen Appliances",
        "output": "pittappillil_kitchen_appliances.json",
        "subcategories": {

            "air-fryer": {
                "url": f"{BASE_URL}/stores/Air%20Fryer",
                "label": "Air Fryer",
            },

            "appachatty": {
                "url": f"{BASE_URL}/stores/appachatty",
                "label": "Appachatty",
            },

            "barbeque": {
                "url": f"{BASE_URL}/stores/Barbeque",
                "label": "Barbeque",
            },

            "biriyani-pot": {
                "url": f"{BASE_URL}/stores/biriyanipot",
                "label": "Biriyani Pot",
            },

            "casserole": {
                "url": f"{BASE_URL}/stores/CASSEROLE",
                "label": "Casserole",
            },

            "chimney-hob": {
                "url": f"{BASE_URL}/stores/Chimney%20%26%20Hob",
                "label": "Chimney & Hob",
            },

            "cloth-dryer": {
                "url": f"{BASE_URL}/stores/clothdryer",
                "label": "Cloth Dryer",
            },

            "cooking-range": {
                "url": f"{BASE_URL}/stores/Cooking%20Range",
                "label": "Cooking Range",
            },

            "cookware-set": {
                "url": f"{BASE_URL}/stores/cookwareset",
                "label": "Cookware Set",
            },

            "electric-kettle": {
                "url": f"{BASE_URL}/stores/ELECTRIC%20KETTLE",
                "label": "Electric Kettle",
            },

            "emergency-light": {
                "url": f"{BASE_URL}/stores/emergency-light",
                "label": "Emergency Light",
            },

            "flask": {
                "url": f"{BASE_URL}/stores/kitchenappliancesvaccumflask",
                "label": "Flask",
            },

            "food-processor": {
                "url": f"{BASE_URL}/stores/Food%20Processor",
                "label": "Food Processor",
            },

            "gas-stove": {
                "url": f"{BASE_URL}/stores/gas-stove",
                "label": "Gas Stove",
            },

            "hand-blender": {
                "url": f"{BASE_URL}/stores/hand-blender",
                "label": "Hand Blender",
            },

            "home-inverters": {
                "url": f"{BASE_URL}/stores/home_inverters",
                "label": "Home Inverters & Batteries",
            },

            "induction-cooker": {
                "url": f"{BASE_URL}/stores/induction-cooker",
                "label": "Induction Cooker",
            },

            "ironing-board": {
                "url": f"{BASE_URL}/stores/ironingboard",
                "label": "Ironing Board",
            },

            "iron-box": {
                "url": f"{BASE_URL}/stores/iron-box",
                "label": "Iron Box",
            },

            "juicer-mxr-grinder": {
                "url": f"{BASE_URL}/stores/juicer-mxr-grinder",
                "label": "Juicer Mxr Grinder",
            },

            "mixer-grinders": {
                "url": f"{BASE_URL}/stores/mixer-grinders",
                "label": "Mixer Grinders",
            },

            "microwave-oven": {
                "url": f"{BASE_URL}/stores/mw-oven",
                "label": "Microwave Oven",
            },

            "noodle-maker": {
                "url": f"{BASE_URL}/stores/idiyappammaker",
                "label": "Noodle Maker",
            },

            "oven-toaster-grills": {
                "url": f"{BASE_URL}/stores/oven-toaster-grills",
                "label": "Oven Toaster Grills",
            },

            "popcorn-maker": {
                "url": f"{BASE_URL}/stores/POPCORN%20MAKER",
                "label": "Popcorn Maker",
            },

            "pressure-cooker": {
                "url": f"{BASE_URL}/stores/PRESSURE%20COOKERS",
                "label": "Pressure Cooker",
            },

            "rice-cooker": {
                "url": f"{BASE_URL}/stores/RICE%20COOKER",
                "label": "Rice Cooker",
            },

            "soda-maker": {
                "url": f"{BASE_URL}/stores/soda-maker",
                "label": "Soda Maker",
            },

            "stand-mixer": {
                "url": f"{BASE_URL}/stores/Stand-Mixer",
                "label": "Stand Mixer",
            },

            "vacuum-cleaners": {
                "url": f"{BASE_URL}/stores/vacuum-cleaners",
                "label": "Vacuum Cleaners",
            },

            "voltage-stabilizer": {
                "url": f"{BASE_URL}/stores/voltage-stabiliser",
                "label": "Voltage Stabilizer",
            },

            "water-cooler": {
                "url": f"{BASE_URL}/stores/WATER_COOLER",
                "label": "Water Cooler",
            },

            "water-dispenser": {
                "url": f"{BASE_URL}/stores/WATER%20DISPENSER",
                "label": "Water Dispenser",
            },

            "water-heater": {
                "url": f"{BASE_URL}/stores/water-heater",
                "label": "Water Heater",
            },

            "wet-grinder": {
                "url": f"{BASE_URL}/stores/wet-grinder",
                "label": "Wet Grinder",
            },

            "water-purifier": {
                "url": f"{BASE_URL}/stores/-water-purifier",
                "label": "Water Purifier",
            },
        },
    },

    # --------------------------------------------------------
    # Home Appliances
    # --------------------------------------------------------

    "home-appliances": {
        "label": "Home Appliances",
        "output": "pittappillil_home_appliances.json",
        "subcategories": {

            "split-ac": {
                "url": f"{BASE_URL}/stores/SPLIT%20AC",
                "label": "Split AC",
            },

            "chest-freezers": {
                "url": f"{BASE_URL}/stores/CHEST%20FREEZERS",
                "label": "Chest Freezers",
            },

            "washing-machines": {
                "url": f"{BASE_URL}/stores/washing-machine",
                "label": "Washing Machines",
            },

            "washer-dryers-dryers": {
                "url": f"{BASE_URL}/stores/washer-dryers-dryers",
                "label": "Washer Dryers/Dryers",
            },

            "dish-washer": {
                "url": f"{BASE_URL}/stores/dish-washer",
                "label": "Dish Washer",
            },

            "refrigerator": {
                "url": f"{BASE_URL}/stores/refrigerator",
                "label": "Refrigerator",
            },

            "television": {
                "url": f"{BASE_URL}/stores/television",
                "label": "Television",
            },

            "visi-cooler": {
                "url": f"{BASE_URL}/stores/VISI%20COOLER",
                "label": "Visi Cooler",
            },
        },
    },

    # --------------------------------------------------------
    # Home Audio
    # --------------------------------------------------------

    "home-audio": {
        "label": "Home Audio",
        "output": "pittappillil_home_audio.json",
        "subcategories": {

            "home-theatre": {
                "url": f"{BASE_URL}/stores/home-theatre",
                "label": "Home Theatre",
            },

            "sound-bar": {
                "url": f"{BASE_URL}/stores/soundbar",
                "label": "Sound Bar",
            },
        },
    },

    # --------------------------------------------------------
    # Air Quality and Circulation
    # --------------------------------------------------------

    "air-quality": {
        "label": "Air Quality and Circulation",
        "output": "pittappillil_air_quality.json",
        "subcategories": {

            "ceiling-fan": {
                "url": f"{BASE_URL}/stores/ceiling",
                "label": "Ceiling Fan",
            },

            "cooler": {
                "url": f"{BASE_URL}/stores/cooler",
                "label": "Cooler",
            },

            "pedestal-fan": {
                "url": f"{BASE_URL}/stores/pedestal",
                "label": "Pedestal Fan",
            },

            "table-fan": {
                "url": f"{BASE_URL}/stores/table",
                "label": "Table Fan",
            },

            "wall-fan": {
                "url": f"{BASE_URL}/stores/wall",
                "label": "Wall Fan",
            },
        },
    },

    # --------------------------------------------------------
    # Mobiles, Laptops and More
    # --------------------------------------------------------

    "mobiles-laptops": {
        "label": "Mobiles, Laptops and More",
        "output": "pittappillil_mobiles_laptops.json",
        "subcategories": {

            "mobiles": {
                "url": f"{BASE_URL}/stores/Mobile",
                "label": "Mobile Phones",
            },

            "laptops": {
                "url": f"{BASE_URL}/stores/LAPTOP",
                "label": "Laptops",
            },

            "smart-watch": {
                "url": f"{BASE_URL}/stores/Smart%20Watch",
                "label": "Smart Watch",
            },

            "mobile-accessories": {
                "url": f"{BASE_URL}/stores/Mobile_Accessories",
                "label": "Mobile Accessories",
            },
        },
    },
}


# ============================================================
# SELECTORS
# ============================================================

PRODUCT_CARD_SELECTOR = ".products-list__item"

PRODUCT_NAME_SELECTOR = ".product-card__name a"

PRICE_SELECTOR = ".product-card__prices"

AVAILABILITY_SELECTOR = ".product-card__availability span"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

log = logging.getLogger("pittappillil")


# ============================================================
# PRICE CLEANING
# ============================================================

def clean_price(price_text):
    """
    Convert a price such as:

        ₹ 35999
        ₹ 35,999
        ₹ 35,999.00

    into:

        35999
    """

    if not price_text:
        return None

    cleaned = price_text.strip()

    cleaned = cleaned.replace(",", "")

    cleaned = re.sub(r"[^\d.]", "", cleaned)

    if not cleaned:
        return None

    try:
        return int(float(cleaned))
    except ValueError:
        return None


# ============================================================
# AVAILABILITY
# ============================================================

def normalize_availability(value):
    """
    Convert Pittappillil's availability text into
    Quote Yard's common format.
    """

    if not value:
        return None

    text = " ".join(value.split()).strip().lower()

    if any(
        phrase in text
        for phrase in (
            "out of stock",
            "out-of-stock",
            "sold out",
            "unavailable",
        )
    ):
        return "Out of stock"

    if any(
        phrase in text
        for phrase in (
            "in stock",
            "in stocks",
            "available",
        )
    ):
        return "In stock"

    return value.strip()


# ============================================================
# URL
# ============================================================

def make_absolute_url(url):
    """
    Convert relative product URLs into absolute URLs.
    """

    if not url:
        return None

    return urljoin(BASE_URL, url)


def build_page_url(base_url, page_number):
    """
    Add/update the page parameter.

    Example:

        /stores/Mobile
        ->
        /stores/Mobile?page=2&limit=12
    """

    parsed = urlparse(base_url)

    query = parse_qs(
        parsed.query,
        keep_blank_values=True,
    )

    query["page"] = [str(page_number)]

    if "limit" not in query:
        query["limit"] = [str(PAGE_LIMIT)]

    new_query = urlencode(
        query,
        doseq=True,
    )

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


# ============================================================
# RESOURCE BLOCKING
# ============================================================

BLOCKED_RESOURCE_TYPES = {
    "image",
    "media",
    "font",
}


def handle_route(route):
    """
    Block resources we don't need for product extraction.
    """

    if route.request.resource_type in BLOCKED_RESOURCE_TYPES:
        route.abort()
    else:
        route.continue_()


# ============================================================
# PRICE EXTRACTION
# ============================================================

def extract_current_price(card):
    """
    Pittappillil structure:

        <div class="product-card__prices">
            ₹ 35999
            <small>
                <strike>₹ 58999</strike>
            </small>
        </div>

    We need only the direct text node containing
    the CURRENT price.

    The <strike> original price is ignored.
    """

    price_element = card.locator(
        PRICE_SELECTOR
    )

    if price_element.count() == 0:
        return None

    try:
        price_text = price_element.first.evaluate(
            """
            element => {
                const directTextNodes = Array.from(
                    element.childNodes
                ).filter(
                    node => node.nodeType === Node.TEXT_NODE
                );

                return directTextNodes
                    .map(node => node.textContent.trim())
                    .filter(Boolean)
                    .join(" ");
            }
            """
        )

    except Exception as exc:
        log.warning(
            "Could not extract current price: %s",
            exc,
        )
        return None

    return clean_price(price_text)


# ============================================================
# SCRAPE ONE PAGE
#
# Returns raw products (name/price/url/availability/shop) with
# NO category/subcategory tagging. Tagging happens one level up,
# in scrape_subcategory(), which is the only place that knows
# both the main category and the subcategory being scraped.
# ============================================================

def scrape_page(
    page,
    url,
    context_label,
):
    """
    Scrape all products from one subcategory page.

    context_label is used for logging only, e.g.
    "Kitchen Appliances > Air Fryer".
    """

    log.info(
        "[%s] Opening %s",
        context_label,
        url,
    )

    try:
        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

    except PlaywrightTimeoutError:
        log.warning(
            "[%s] Page load timeout",
            context_label,
        )
        return []

    except Exception as exc:
        log.warning(
            "[%s] Navigation error: %s",
            context_label,
            exc,
        )
        return []

    # --------------------------------------------------------
    # HTTP STATUS
    # --------------------------------------------------------

    if response:

        status = response.status

        if status == 403:
            log.warning(
                "[%s] 403 Forbidden. Stopping subcategory.",
                context_label,
            )
            return []

        if status == 404:
            log.warning(
                "[%s] 404 Page not found. Stopping subcategory.",
                context_label,
            )
            return []

        if status >= 500:
            log.warning(
                "[%s] Server returned %s. Stopping subcategory.",
                context_label,
                status,
            )
            return []

    # --------------------------------------------------------
    # PRODUCT CARDS
    # --------------------------------------------------------

    try:
        page.wait_for_selector(
            PRODUCT_CARD_SELECTOR,
            timeout=10000,
        )

    except PlaywrightTimeoutError:
        log.info(
            "[%s] No product cards found.",
            context_label,
        )
        return []

    cards = page.locator(
        PRODUCT_CARD_SELECTOR
    )

    card_count = cards.count()

    log.info(
        "[%s] Found %d product cards.",
        context_label,
        card_count,
    )

    products = []

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    for index in range(card_count):

        card = cards.nth(index)

        try:

            # ------------------------------------------------
            # NAME + URL
            # ------------------------------------------------

            name_link = card.locator(
                PRODUCT_NAME_SELECTOR
            ).first

            name = name_link.inner_text().strip()

            product_url = name_link.get_attribute(
                "href"
            )

            product_url = make_absolute_url(
                product_url
            )

            # ------------------------------------------------
            # PRICE
            # ------------------------------------------------

            price = extract_current_price(
                card
            )

            # ------------------------------------------------
            # AVAILABILITY
            # ------------------------------------------------

            availability_locator = card.locator(
                AVAILABILITY_SELECTOR
            )

            if availability_locator.count() > 0:

                availability_text = (
                    availability_locator
                    .first
                    .inner_text()
                    .strip()
                )

            else:

                availability_text = None

            availability = normalize_availability(
                availability_text
            )

            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            if not name:
                log.warning(
                    "[%s] Skipping product with no name.",
                    context_label,
                )
                continue

            if not product_url:
                log.warning(
                    "[%s] Skipping product with no URL: %s",
                    context_label,
                    name,
                )
                continue

            # ------------------------------------------------
            # RAW QUOTE YARD FORMAT
            # (category / subcategory added by the caller)
            # ------------------------------------------------

            product = {
                "name": name,
                "price": price,
                "url": product_url,
                "availability": availability,
                "shop": SHOP_NAME,
            }

            products.append(product)

        except Exception as exc:

            log.warning(
                "[%s] Failed to parse product %d: %s",
                context_label,
                index + 1,
                exc,
            )

    return products


# ============================================================
# SCRAPE ONE SUBCATEGORY (all its pages)
# ============================================================

def scrape_subcategory(
    browser,
    category_label,
    subcategory_key,
    subcategory_config,
    max_pages=None,
):
    """
    Scrape all pages of one Pittappillil subcategory and tag
    every product with both the main category label and the
    subcategory label.
    """

    subcategory_label = subcategory_config["label"]

    base_url = subcategory_config["url"]

    context_label = f"{category_label} > {subcategory_label}"

    log.info("")
    log.info("-" * 70)
    log.info(
        "SUBCATEGORY: %s",
        context_label,
    )
    log.info("-" * 70)

    context = browser.new_context(
        viewport={
            "width": 1440,
            "height": 900,
        }
    )

    context.route(
        "**/*",
        handle_route,
    )

    page = context.new_page()

    all_products = []

    seen_urls = set()

    page_number = 1

    page_limit = (
        max_pages
        if max_pages is not None
        else SAFETY_MAX_PAGES
    )

    try:

        while page_number <= page_limit:

            page_url = build_page_url(
                base_url,
                page_number,
            )

            log.info(
                "[%s] Scraping page %d",
                context_label,
                page_number,
            )

            products = scrape_page(
                page,
                page_url,
                context_label,
            )

            # ------------------------------------------------
            # No products = subcategory finished
            # ------------------------------------------------

            if not products:

                log.info(
                    "[%s] No products found. "
                    "Stopping pagination.",
                    context_label,
                )

                break

            # ------------------------------------------------
            # Tag + deduplicate
            # ------------------------------------------------

            new_products = 0

            for product in products:

                product_url = product["url"]

                if product_url in seen_urls:
                    continue

                seen_urls.add(product_url)

                product["category"] = category_label
                product["subcategory"] = subcategory_label

                all_products.append(product)

                new_products += 1

            log.info(
                "[%s] Page %d: %d products, %d new.",
                context_label,
                page_number,
                len(products),
                new_products,
            )

            # ------------------------------------------------
            # Same products repeated
            # ------------------------------------------------

            if new_products == 0:

                log.info(
                    "[%s] No new products found. "
                    "Stopping pagination.",
                    context_label,
                )

                break

            page_number += 1

            page.wait_for_timeout(
                PAGE_DELAY_MS
            )

        else:

            log.warning(
                "[%s] Reached safety limit of %d pages.",
                context_label,
                page_limit,
            )

    finally:

        page.close()
        context.close()

    log.info(
        "[%s] Total unique products: %d",
        context_label,
        len(all_products),
    )

    return all_products


# ============================================================
# SCRAPE ONE MAIN CATEGORY (loops its subcategories)
# ============================================================

def scrape_category(
    browser,
    category_key,
    category_config,
    max_pages=None,
    selected_subcategories=None,
):
    """
    Scrape every subcategory under one main category and
    return the combined product list (one list -> one JSON
    file per main category).
    """

    category_label = category_config["label"]

    subcategories = category_config["subcategories"]

    if selected_subcategories:

        subcategories = {
            key: config
            for key, config in subcategories.items()
            if key in selected_subcategories
        }

        unknown_subcategories = (
            set(selected_subcategories)
            - set(subcategories)
        )

        if unknown_subcategories:

            log.warning(
                "[%s] Unknown subcategories: %s",
                category_label,
                ", ".join(sorted(unknown_subcategories)),
            )

    log.info("")
    log.info("=" * 70)
    log.info(
        "CATEGORY: %s (%d subcategories)",
        category_label,
        len(subcategories),
    )
    log.info("=" * 70)

    all_products = []

    for subcategory_key, subcategory_config in subcategories.items():

        try:

            products = scrape_subcategory(
                browser=browser,
                category_label=category_label,
                subcategory_key=subcategory_key,
                subcategory_config=subcategory_config,
                max_pages=max_pages,
            )

            all_products.extend(products)

        except Exception:

            log.exception(
                "[%s] Subcategory failed: %s",
                category_label,
                subcategory_config["label"],
            )

            # Continue with the next subcategory.
            continue

    log.info(
        "[%s] Total products across all subcategories: %d",
        category_label,
        len(all_products),
    )

    return all_products


# ============================================================
# SAVE JSON
# ============================================================

def save_products(
    category_config,
    products,
):
    """
    Save one JSON snapshot for the whole main category
    (all of its subcategories combined).
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = DATA_DIR / category_config["output"]

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            products,
            file,
            ensure_ascii=False,
            indent=2,
        )

    log.info(
        "Saved %d products -> %s",
        len(products),
        output_path,
    )


# ============================================================
# RUN SCRAPER
# ============================================================

def run_scraper(
    selected_categories=None,
    selected_subcategories=None,
    max_pages=None,
    headless=False,
):
    """
    Run the Pittappillil scraper.

    selected_categories filters which main categories run
    (e.g. ["kitchen-appliances"]).

    selected_subcategories filters which subcategories run
    *within* whichever categories are selected (e.g. ["mobiles"]).
    Only meaningful together with a narrow --only; if a name
    doesn't exist in a given category it's simply not found there.
    """

    if selected_categories:

        categories_to_scrape = {
            key: config
            for key, config in CATEGORIES.items()
            if key in selected_categories
        }

        unknown_categories = (
            set(selected_categories)
            - set(categories_to_scrape)
        )

        if unknown_categories:

            log.warning(
                "Unknown categories: %s",
                ", ".join(
                    sorted(unknown_categories)
                ),
            )

    else:

        categories_to_scrape = CATEGORIES

    log.info(
        "Starting Pittappillil scraper."
    )

    log.info(
        "Categories: %d",
        len(categories_to_scrape),
    )

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=headless,
        )

        try:

            for category_key, category_config in (
                categories_to_scrape.items()
            ):

                try:

                    products = scrape_category(
                        browser=browser,
                        category_key=category_key,
                        category_config=category_config,
                        max_pages=max_pages,
                        selected_subcategories=selected_subcategories,
                    )

                    save_products(
                        category_config,
                        products,
                    )

                except Exception:

                    log.exception(
                        "Category failed: %s",
                        category_config["label"],
                    )

                    # Continue with the next category.
                    continue

        finally:

            browser.close()

    log.info("")
    log.info(
        "Pittappillil scraping complete."
    )


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Quote Yard Pittappillil scraper"
        )
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chromium without opening a window.",
    )

    parser.add_argument(
        "--only",
        nargs="+",
        help=(
            "Scrape selected main categories only. "
            "Example: --only kitchen-appliances mobiles-laptops"
        ),
    )

    parser.add_argument(
        "--subcategories",
        nargs="+",
        help=(
            "Within the selected categories, scrape only these "
            "subcategories. Example: "
            "--only mobiles-laptops --subcategories mobiles laptops"
        ),
    )

    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help=(
            "Maximum pages per subcategory. "
            "Default: 100 safety limit."
        ),
    )

    args = parser.parse_args()

    run_scraper(
        selected_categories=args.only,
        selected_subcategories=args.subcategories,
        max_pages=args.max_pages,
        headless=args.headless,
    )


if __name__ == "__main__":
    main()
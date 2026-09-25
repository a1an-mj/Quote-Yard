Quote Yard — Project Master Plan

Project Overview

Quote Yard is a retail price comparison platform focused initially on Kerala/India retailers.

The system will collect product listings and prices from multiple retailers, normalize the data, store it in PostgreSQL, match equivalent products, and present price comparisons through a React frontend.
Target retailers

myG
Oxygen
Pittappillil
Nandilath G-Mart
Croma

Main product categories

Mobiles
Laptops / desktops
Tablets
Accessories
TVs
Home & Kitchen
Refrigerators
Washing Machines
Air Conditioners
Small Appliances
Personal Care
Home Automation
Other retailer categories as needed

2. Core Architecture

Retailer Websites
|
v
Playwright Scrapers
|
v
Raw Product Data
|
v
Data Cleaning / Normalization
|
v
Product Matching
|
v
PostgreSQL
|
v
FastAPI
|
v
React Frontend

A scheduler will trigger the scraping system automatically.
3. Major Modules

Scraping / Data Collection

Collect product information from each retailer.

Current common data model:

name
price
url
availability
shop
category

The scraper should primarily collect what the retailer actually displays.

Important decision: Do not try to perfectly parse every product's RAM, storage, processor, color, etc. across every category. Retailer naming is inconsistent. Preserve reliable raw listing data first.
2. Data Cleaning / Normalization

Make data from different retailers consistent.

Examples:

myG:
Samsung Galaxy S25 5G | 12 GB | 256 GB

Oxygen:
Samsung S25 12/256GB

Pittappillil:
SAMSUNG GALAXY S25 5G 256 GB

Eventually these need to be normalized so the system can determine whether they represent the same product/variant.
3. Product Matching

One of the hardest parts of Quote Yard.

The system must distinguish:

Galaxy S25 256GB
Galaxy S25 Ultra 256GB
Galaxy S25 512GB

Possible matching signals:

Brand
Product/model name
Model number
Variant
Storage
RAM where applicable
Color where reliable
Category-specific identifiers

Product matching stays separate from scraping.
4. Database

Database: PostgreSQL

ORM: SQLAlchemy

Future concepts:

Retailers
Products
Product Variants
Categories
Retailer Listings
Prices
Price History

Conceptually:

Canonical Product
|
+---- myG listing
+---- Oxygen listing
+---- Pittappillil listing
+---- Nandilath G-Mart listing
+---- Croma listing

Backend

Technology: FastAPI

React
|
v
FastAPI
|
v
SQLAlchemy
|
v
PostgreSQL

Possible future endpoints:

GET /products
GET /products/{id}
GET /products/{id}/prices
GET /search?q=samsung
GET /compare/{product_id}

Search

Initially simple database-backed search is enough.

User → React → FastAPI → PostgreSQL → Results

Do not over-engineer search initially.
7. Comparison

Show equivalent products across retailers:

Samsung Galaxy S25 256GB

myG           ₹39,999
Oxygen        ₹40,499
Pittappillil  ₹40,999
Croma         ₹41,999

This depends heavily on product matching.
8. Scheduler

Technology: APScheduler

Example:

02:00 AM
|
v
Run retailer scrapers
|
v
Process data
|
v
Update PostgreSQL

One retailer failing should not stop the whole update.
9. Frontend

Technology:

React
Vite
Tailwind CSS / utility styling
React Router

Prototype flow:

Landing
↓
Sign Up / Login
↓
Dashboard
↓
Search
↓
Product Results
↓
Product Comparison

Frontend Design

Visual direction:

Terracotta primary
Warm Ivory
Warm Taupe
Olive Green
Walnut Brown
Near Black

Approximate palette:

Terracotta   #C65A3A
Warm Ivory   #F5EFE5
Warm Taupe   #A99B8D
Olive Green  #656A45
Walnut Brown #4A3025
Near Black   #171512

Style:

Neo-brutalist / playful brutalist
Bold chunky typography
Rounded cards
Strong dark framing
High contrast
Solid color blocks
Subtle shadows
Minimal gradients
Mobile-first
Responsive
Subtle animations

5. Technology Stack
Frontend

React
Vite
Tailwind CSS
React Router

Backend

Python
FastAPI
SQLAlchemy

Database

PostgreSQL

Scraping

Python
Playwright
Chromium

Scheduling

APScheduler

Development

Git
GitHub

Deployment is not finalized yet. An Asus VivoBook may be used as an experimental/self-hosted server later.
6. Important Technology Decisions
No OpenAI extraction

Quote Yard will not use OpenAI AI extraction for scraping.

Scraping uses deterministic techniques:

Playwright
CSS selectors
DOM extraction
normalization rules

Avoid premature complexity

Do not add these for the MVP unless a real requirement appears:

Kafka
RabbitMQ
Celery
Redis
Kubernetes
complicated AI extraction
complex search engines
microservices

The MVP stack is:

React
+
FastAPI
+
PostgreSQL
+
SQLAlchemy
+
Playwright
+
APScheduler

Current Repository

quote-yard/
├── data/
├── frontend/
├── scrapers/
├── tests/
├── utils/
├── .git/
├── .gitignore
└── .venv/

Main unified MyG scraper:

scrapers/myg_scraper.py

Data is stored under:

data/

GitHub repository:

git@github.com/Quote-Yard.git

Main branch:

main

Current MyG Scraper

The MyG scraper uses one configuration dictionary:

CATEGORIES = {
"mobiles": {...},
"laptops": {...},
"tablets": {...},
"accessories": {...},
"home-kitchen": {...},
"refrigerators": {...},
"washing-machines": {...},
"air-conditioners": {...},
"small-appliances": {...},
"personal-care": {...},
"home-automation": {...},
}

Each category defines:

base_url
output
label

Current selectors:

PRODUCT_LINK_SELECTOR = "a.line-clamp-2"
PRICE_SELECTOR = '[id^="sec_discounted_price_"]'
AVAILABILITY_SELECTOR = "p.text-green"

Each product currently becomes:

{
"name": "...",
"price": 39999,
"url": "...",
"availability": "In stock",
"shop": "myG",
"category": "Mobiles"
}

MyG Price Cleaning

Example:

₹1,23,456.00

becomes:

123456

clean_price() removes currency symbols, commas and spaces, then converts the value to an integer. Invalid values become None.
10. MyG Pagination

The scraper constructs direct URLs:

Page 1:
https://www.myg.in/category/

Page 2:
https://www.myg.in/category/page-2/

Page 3:
https://www.myg.in/category/page-3/

It does not click pagination buttons.

This is intentional because the website's pagination behavior can differ from direct page navigation.

Safety limit:

SAFETY_MAX_PAGES = 100

MyG Navigation Edge Cases
403

Some pages can return:

403 Forbidden

Example encountered:

/mobile-phones/page-10/

The scraper stops that category cleanly.
404

Some categories have fewer pages.

Example:

/home-automation/page-3/

does not exist. Before the fix, the scraper waited 10 seconds for a.line-clamp-2, hit a TimeoutError, and crashed. The crash also skipped saving, so products already collected from earlier pages were lost (Home Automation had 23 from pages 1–2).

Status: fixed. scrape_category() now checks the HTTP response right after page.goto(), before the product selector is called:

response = page.goto(url, wait_until="domcontentloaded")

if response and response.status == 404:
log.warning("Page does not exist (404). Stopping category.")
break

if response and response.status == 403:
log.warning("MyG returned 403 Forbidden. Stopping category.")
break

This preserves already-collected products and allows them to be saved.

Fallback (only if needed): if a missing page ever returns 200 with an empty grid, or redirects, instead of a real 404, wrap page.wait_for_selector() in scrape_page() with a try/except PlaywrightTimeoutError that returns an empty list. The existing "No products found. Stopping category." check then ends the category cleanly.
12. MyG Resource Management

A major issue encountered was:

ERR_INSUFFICIENT_RESOURCES

The actual page could be opened normally in Firefox, so the page itself was valid. The problem was likely Chromium resource usage during a long scrape.

Current strategy:
Block unnecessary resources

BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}

The current JSON does not need these resources.
Fresh page per category

Current architecture:

Browser
|
Context
|
+-- Page → Mobiles → close
+-- Page → Laptops → close
+-- Page → Tablets → close
+-- Page → Accessories → close
+-- Page → Home & Kitchen → close
+-- ...

This avoids keeping every category page alive.

A new browser is not required for every category.
12a. Oxygen Digital Shop Scraper

Second retailer scraper, built after MyG stabilized: scrapers/oxygen_scraper.py.

Same MVP field model as MyG (name, price, url, availability, shop, category). Does not visit product-detail pages or parse RAM/storage from names.
Site differences from MyG

Oxygen runs on Shopify, which changes several things from MyG's custom PHP storefront:

            MyG                          Oxygen

Selectors       CSS on visible text          data-* attributes on the card
(a.line-clamp-2, etc.)        (data-product-title,
data-product-price,
data-product-url)
Pagination      /category/page-2/             ?page=2 (or &page=2)
Price format    Already rupees with           Paise (divide by 100)
₹/commas to strip

Selectors and config

PRODUCT_CARD_SELECTOR = "div.custom-product-card"
PRODUCT_TITLE_ATTRIBUTE = "data-product-title"
PRODUCT_PRICE_ATTRIBUTE = "data-product-price"
PRODUCT_URL_ATTRIBUTE = "data-product-url"

clean_price() treats the card's price attribute as paise (e.g. 1349900 → ₹13,499) and divides by 100.
Extra robustness over the MyG scraper

Built with a few defensive additions MyG doesn't have yet:

5xx handling: any status >= 500 stops the category cleanly, not just 403/404.
Per-page try/except: scrape_category() wraps each page fetch in a try/except, logs, and breaks cleanly on an unexpected error instead of crashing the whole run.
URL dedup + stop condition: tracks seen_urls; if a page returns zero new URLs, the category stops. Protects against a site serving the same page repeatedly instead of a clean 404.
detect_availability() fallback chain: scans the card's full text first for "out of stock" / "sold out" / "add to cart"; if that's inconclusive, checks each button/a inside the card individually for the same phrases.
500ms delay between pages (page.wait_for_timeout), and an explicit 1440x900 viewport on the context.

Category URLs — verification status

CATEGORIES covers: mobiles, laptops, kitchen-appliances, refrigerators, washing-machines, inverter, battery, gadgets, monitors, printers, led-tv. Only the URL slug was known to be right by guessing from the pattern used elsewhere on the site; each needs checking against the live site before trusting it.

Verified:

mobiles — the guessed slug /collections/mobile-phones was wrong. Correct slug is /collections/mobile-smart-phones. Fixed and confirmed: names, prices, URLs, and availability all populated correctly on a real scrape; the paise/100 price conversion is confirmed correct against real prices (e.g. ₹13,499 Galaxy A07, ₹1,39,999 Galaxy S26 Ultra).
All categories — a full headless run across every category in CATEGORIES completed successfully. Pagination (?page=N), the URL-dedup "no new products" stop condition, and every category URL slug all confirmed working end to end.

Availability check

Oxygen's own site-side "Availability" filter facet on the mobiles collection lists only "In stock" (58 of 58 products) — there is no "Out of stock" facet at all, meaning nothing in that category is currently out of stock on the real site. So detect_availability()'s in-stock path is confirmed correct against real data, but its out-of-stock path can't be exercised yet — not a scraper gap, just nothing on the site to test it against right now. Revisit if a product goes out of stock later, or check a different category.
Status: Oxygen scraper considered done for MVP scope

With category URLs, pagination, price conversion, and availability all verified, Oxygen is at the same maturity level as MyG. Next retailer per the roadmap is Pittappillil.
Naming inconsistency observed within Oxygen itself

Not just across retailers — Oxygen's own listings aren't consistent with each other:

Most listings:
Samsung Galaxy A07 5G (Black, 128 GB) (6 GB RAM)

Some listings (myG-style pipes):
realme 16 Pro+ 5G | 12 GB | 256 GB | Master Gold

Relevant for the later normalization/matching phase — can't assume one name format per retailer.

Also observed: likely duplicate listings for the same physical product under slightly different slugs/names, e.g.:

vivo-v70-fe-northern-lights-purple-8gb-256gb   (name has "2026" suffix)
vivo-v70fe-northern-lights-purple-8gb-256gb    (no "2026", no space in "v70fe")

Not a scraper bug — Oxygen's own site appears to have two listings for the same product. Worth keeping in mind for matching, not something to fix in the scraper.
Oxygen Scraper Commands

All categories:

python scrapers/oxygen_scraper.py

Headless:

python scrapers/oxygen_scraper.py --headless

Selected categories:

python scrapers/oxygen_scraper.py --only mobiles laptops

One category, limited pages (used for the mobiles verification test):

python scrapers/oxygen_scraper.py --only laptops --max-pages 1

MyG Scraper Commands

All categories:

python scrapers/myg_scraper.py

Headless:

python scrapers/myg_scraper.py --headless

Selected categories:

python scrapers/myg_scraper.py --only mobiles tablets

One category:

python scrapers/myg_scraper.py --only home-automation

Page safety limit:

python scrapers/myg_scraper.py --max-pages 20

Existing MyG Work
Mobiles

Previously collected approximately 108 products before encountering a 403 at page 10.

Mobile parsing extracted:

RAM
Storage
Color

Some feature phones legitimately had no normal RAM field.

Important discovery: product names and URLs can disagree on variants/colors/storage.

Displayed product name is more trustworthy for variant information than blindly deriving information from URLs.

Mobile data is considered good enough for now.
Laptops

Laptop names were inconsistent, especially Apple products, gaming laptops and desktop/AIO listings.

A processor parser was improved and tested with examples such as:

AMD Ryzen 7
AMD Ryzen 5
Intel Core i3
Intel Core i5
Intel Core Ultra 5 225H
M5 Pro Chip
Intel Core i7 14700HX
AMD Ryzen 7 7735HS

Laptop parsing is considered good enough for now.
Tablets

Use the simple listing approach:

name = product["name"].split("|")[0].strip()

Keep:

name
price
url
availability
shop
category

Duplicate listings and missing availability were observed and are not being over-engineered yet.
TVs

Same simple approach.
Accessories

Same simple approach.
15. Product Parsing Strategy Going Forward

For new categories:

Do not over-parse specifications.

Prefer:

Raw listing
↓
name
price
url
availability
shop
category

Only add category-specific parsing when there is a real requirement.

This prevents inconsistent retailer naming from making the project unnecessarily complicated.
16. JSON Saving

Current saving behavior replaces the existing JSON snapshot.

It does not append.

Example:

Old:
Phone A
Phone B

New scrape:
Phone A
Phone C

Result:

Phone A
Phone C

This is intentional for the current snapshot stage.

Later, PostgreSQL will store price history separately.
17. Debugging Rule

Always debug in this order:

Fix 1
↓
Test once
↓
If broken → Fix 2
↓
Test once
↓
If still broken → Fix 1 + Fix 2
↓
Test once

Do not change multiple unrelated things before testing.

Use one test for each change.

This makes it clear what actually solved the issue.
18. Development Environment

Current environment:

Arch Linux
Python 3.14.6
.venv
Playwright
Chromium

Playwright reported that Arch Linux was not officially supported and downloaded a fallback Ubuntu 24.04 Chromium build, but the browser works.

A previous Python file named inspect.py shadowed Python's standard-library inspect module. It was renamed to:

inspect_page.py

Implementation Roadmap
Phase 1 — Data Collection

MyG        (stable, 404 fix applied)
↓
Oxygen     (done — all categories verified: URLs, pagination, price, availability)
↓
Pittappillil  (done — tested successfully)
↓
Nandilath G-Mart
↓
Croma

Build and stabilize each scraper.
Phase 2 — Data Processing

Raw data
↓
Cleaning
↓
Normalization
↓
Duplicate handling

Phase 3 — PostgreSQL

Build:

schema
SQLAlchemy models
retailer records
product records
listings
prices
price history

Phase 4 — FastAPI

Build:

product endpoints
search
product detail
comparison
price history

Phase 5 — Product Matching

Match retailer listings into canonical products.
Phase 6 — React Integration

Connect frontend to FastAPI.
Phase 7 — Scheduler

Automate retailer scraping and database updates.
Phase 8 — Deployment

Choose deployment environment and move the application from development to a stable server.
20. Current Status
Completed / substantially completed

Quote Yard concept
Technology direction
Repository setup
Git/GitHub setup
MyG scraping architecture
Mobile scraping
Laptop scraping
Tablet scraping
TV scraping
Accessories pipeline
Basic Home & Kitchen scraping
Resource blocking
Fresh page per category
403 handling
404 handling (added to scrape_category(), see section 11)
Simple raw-listing strategy
Frontend prototype direction
System Requirements + SRS documentation spreadsheet
Oxygen scraper built (scrapers/oxygen_scraper.py), including 5xx handling, per-page try/except, URL dedup stop condition, and a fallback-chain availability check — more defensive than MyG's current scraper
Oxygen scraper fully verified: all category URLs (mobiles slug corrected, rest confirmed by a full headless run), pagination, price conversion, and in-stock availability all confirmed against real scraped data

Pittappillil scraper tested successfully; all configured categories and grouped JSON outputs are working correctly.

Currently being finished

Confirm the unified MyG scraper is robust end to end against:

403
404 (fix applied, needs a confirming run across all categories)
resource exhaustion
categories with different page counts
missing availability
navigation failures

Open items to verify

CATEGORIES in myg_scraper.py has no tvs entry, although TVs are listed as done above. Confirm whether TVs were scraped by an earlier script or still need adding to the config.
Oxygen's own listings are internally inconsistent in naming (see section 12a) and may contain near-duplicate listings for the same product — relevant for the later normalization/matching phase.
Oxygen's out-of-stock availability path (detect_availability() returning "Out of stock") is unverified — nothing on the site is currently out of stock. Revisit later, or check a different category.

Next major work

MyG, Oxygen, and Pittappillil are now stable.

Pittappillil has been tested successfully and is complete for the current MVP scraper scope.

Next major work:
Nandilath G-Mart
↓
Croma
↓
PostgreSQL

Hardest Parts

The main difficult areas are expected to be:
Product matching

Determining whether different retailer listings represent the same product/variant.
Reliable multi-retailer scraping

Every retailer has different HTML, pagination, price formats, availability, and anti-bot behavior.
Database design

Supporting canonical products, retailer listings, variants, current prices and historical prices.
Data quality

Handling duplicates, missing values, inconsistent names, changed URLs and temporary failures.
Automation

Allowing one retailer to fail without stopping the entire update process.
22. What Quote Yard Should Eventually Do

Retailer Websites
|
v
Scrapers
|
v
Data Normalization
|
v
Product Matching
|
v
PostgreSQL
|
v
FastAPI
|
v
React
|
v
User Search
|
v
Price Comparison

Example final experience:

User searches:

Samsung Galaxy S25

    ↓

Quote Yard finds the relevant product

    ↓

Samsung Galaxy S25 256GB

myG           ₹39,999
Oxygen        ₹40,499
Pittappillil  ₹40,999
Croma         ₹41,999

    ↓

Price history
Availability
Retailer links
Product details

The goal is to build a working end-to-end price comparison system first, then progressively improve matching, data quality, automation and UX.
23. Immediate Next Step

MyG, Oxygen, and Pittappillil scraper work is complete for the current MVP scope.

Pittappillil has been tested successfully and is working correctly.

Next step:
Build the Nandilath G-Mart scraper.

After Nandilath G-Mart:
Croma
↓
PostgreSQL

Do not make unrelated scraper changes while building the next retailer.
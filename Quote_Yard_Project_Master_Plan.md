# 🧱 **QUOTE YARD**

### **Project Master Plan**

> A retail price comparison platform, starting with Kerala / India retailers.

---

## 📑 **Table of Contents**

| # | Section | # | Section |
|---|---------|---|---------|
| 1 | [Project Overview](#1-project-overview) | 13 | [MyG Scraper Commands](#13-myg-scraper-commands) |
| 2 | [Core Architecture](#2-core-architecture) | 14 | [Existing MyG Work](#14-existing-myg-work) |
| 3 | [Major Modules](#3-major-modules) | 15 | [Parsing Strategy](#15-product-parsing-strategy-going-forward) |
| 4 | [Frontend Design](#4-frontend-design) | 16 | [JSON Saving](#16-json-saving) |
| 5 | [Technology Stack](#5-technology-stack) | 17 | [Debugging Rule](#17-debugging-rule) |
| 6 | [Technology Decisions](#6-important-technology-decisions) | 18 | [Dev Environment](#18-development-environment) |
| 7 | [Current Repository](#7-current-repository) | 19 | [Roadmap](#19-implementation-roadmap) |
| 8 | [MyG Scraper](#8-current-myg-scraper) | 19a | [Phase 2A: Data Cleaning](#19a-phase-2a-data-cleaning-) |
| 9 | [MyG Price Cleaning](#9-myg-price-cleaning) | 19b | [Phase 2B: Normalization](#19b-phase-2b-normalization-) |
| 10 | [MyG Pagination](#10-myg-pagination) | 19c | [Phase 2C: Brand Extraction](#19c-phase-2c-brand-extraction-) |
| 11 | [MyG Edge Cases](#11-myg-navigation-edge-cases) | 20 | [Current Status](#20-current-status) |
| 12 | [Resource Mgmt / Oxygen / Pittappillil](#12-myg-resource-management) | 21 | [Hardest Parts](#21-hardest-parts) |
| | | 22 | [Final Goal](#22-what-quote-yard-should-eventually-do) |
| | | 23 | [Immediate Next Step](#23-immediate-next-step) |

---

# 1. **PROJECT OVERVIEW**

Quote Yard is a retail price comparison platform focused initially on **Kerala / India** retailers.

The system will:

1. Collect product listings and prices from multiple retailers
2. Normalize the data
3. Store it in PostgreSQL
4. Match equivalent products
5. Present price comparisons through a React frontend

## 🏪 **Target Retailers**

| Status | Retailer |
|--------|----------|
| ✅ Active | **myG** |
| ✅ Active | **Oxygen** |
| ✅ Active | **Pittappillil** |
| ✅ Active | **Nandilath G Mart** |
| ⏳ Future | **Croma** |

> The scraper / data architecture is designed to be scalable, so retailers such as Croma can be added later **without redesigning the core system**.

## 🛍️ **Product Categories**

Quote Yard has its **own canonical category system**, independent of any retailer's menus. It is defined in `data_processing/taxonomy/taxonomy.json` (14 parent categories, 48 product types) and documented in [Section 19b](#19b-phase-2b-normalization-). Do not list categories by hand here; the taxonomy file is the source of truth.

---

# 2. **CORE ARCHITECTURE**

```
Retailer Websites
   |
   v
Playwright Scrapers
   |
   v
Raw Product Data
   |
   v
Data Cleaning (Phase 2A)
   |
   v
Normalization (Phase 2B)
   |
   v
Brand Extraction (Phase 2C)
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
```

A **scheduler** triggers the scraping system automatically.

---

# 3. **MAJOR MODULES**

## 🕷️ **3.1 Scraping / Data Collection**

Collect product information from each retailer.

**Common data model:**

| Field | Field | Field |
|-------|-------|-------|
| `name` | `price` | `url` |
| `availability` | `shop` | `category` |
| `subcategory` | | |

> ⚠️ **Important decision:** Do **not** try to perfectly parse every product's RAM, storage, processor, color, etc. across every category. Retailer naming is inconsistent. **Preserve reliable raw listing data first.**

## 🧹 **3.2 Data Cleaning / Normalization / Brand Extraction**

Make data from different retailers consistent. Cleaning (2A), normalization (2B) and brand extraction (2C) are separate steps; see Sections 19a, 19b and 19c.

| Retailer | Listing name |
|----------|--------------|
| myG | `Samsung Galaxy S25 5G \| 12 GB \| 256 GB` |
| Oxygen | `Samsung S25 12/256GB` |
| Pittappillil | `SAMSUNG GALAXY S25 5G 256 GB` |

Eventually these must be normalized so the system can decide whether they are the **same product / variant**.

## 🔗 **3.3 Product Matching**

One of the **hardest parts** of Quote Yard. The system must distinguish:

- Galaxy S25 256GB
- Galaxy S25 Ultra 256GB
- Galaxy S25 512GB

**Possible matching signals:**

| | | |
|---|---|---|
| Brand | Product / model name | Model number |
| Variant | Storage | RAM (where applicable) |
| Color (where reliable) | Category-specific identifiers | |

> Product matching stays **separate** from scraping, from normalization and from brand extraction.

## 🗄️ **3.4 Database**

| | |
|---|---|
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy |

**Future concepts:** Retailers · Products · Product Variants · Categories · Retailer Listings · Prices · Price History

```
Canonical Product
   |
   +---- myG listing
   +---- Oxygen listing
   +---- Pittappillil listing
   +---- Nandilath G Mart listing
   +---- Croma listing
```

A listing may belong to **more than one category** (see Section 19a findings), so the schema needs a listing ↔ category join table rather than a single category column. The loading rule is decided in [Section 19b](#19b-phase-2b-normalization-): one listing per `(shop, url)`, one join-table row per distinct `(category, product_type)` seen for that URL.

## ⚙️ **3.5 Backend**

**Technology:** FastAPI

```
React -> FastAPI -> SQLAlchemy -> PostgreSQL
```

**Possible future endpoints:**

| Method | Endpoint |
|--------|----------|
| GET | `/products` |
| GET | `/products/{id}` |
| GET | `/products/{id}/prices` |
| GET | `/search?q=samsung` |
| GET | `/compare/{product_id}` |

## 🔍 **3.6 Search**

Initially, simple database-backed search is enough.

```
User -> React -> FastAPI -> PostgreSQL -> Results
```

> Do **not** over-engineer search initially.

## ⚖️ **3.7 Comparison**

Show equivalent products across retailers:

**Samsung Galaxy S25 256GB**

| Retailer | Price |
|----------|-------|
| myG | ₹39,999 |
| Oxygen | ₹40,499 |
| Pittappillil | ₹40,999 |
| Croma | ₹41,999 |

*This depends heavily on product matching.*

## ⏰ **3.8 Scheduler**

**Technology:** APScheduler

```
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
```

> One retailer failing should **not** stop the whole update.

## 🖥️ **3.9 Frontend**

**Technology:** React · Vite · Tailwind CSS / utility styling · React Router

**Prototype flow:**

```
Landing -> Sign Up / Login -> Dashboard -> Search -> Product Results -> Product Comparison
```

---

# 4. **FRONTEND DESIGN**

**Visual direction:** Terracotta primary, Warm Ivory, Warm Taupe, Olive Green, Walnut Brown, Near Black.

| Color | Hex |
|-------|-----|
| 🟧 Terracotta | `#C65A3A` |
| 🟨 Warm Ivory | `#F5EFE5` |
| 🟫 Warm Taupe | `#A99B8D` |
| 🟩 Olive Green | `#656A45` |
| 🟤 Walnut Brown | `#4A3025` |
| ⬛ Near Black | `#171512` |

**Style:**

| | |
|---|---|
| Neo-brutalist / playful brutalist | Bold chunky typography |
| Rounded cards | Strong dark framing |
| High contrast | Solid color blocks |
| Subtle shadows | Minimal gradients |
| Mobile-first | Responsive |
| Subtle animations | |

---

# 5. **TECHNOLOGY STACK**

| Layer | Technology |
|-------|------------|
| **Frontend** | React, Vite, Tailwind CSS, React Router |
| **Backend** | Python, FastAPI, SQLAlchemy |
| **Database** | PostgreSQL |
| **Scraping** | Python, Playwright, Chromium |
| **Scheduling** | APScheduler |
| **Development** | Git, GitHub |

> Deployment is not finalized yet. An **Asus VivoBook** may be used as an experimental / self-hosted server later.

---

# 6. **IMPORTANT TECHNOLOGY DECISIONS**

## 🚫 **No OpenAI extraction**

Quote Yard will **not** use OpenAI AI extraction for scraping. Scraping uses deterministic techniques:

- Playwright
- CSS selectors
- DOM extraction
- Normalization rules

## 🪶 **Avoid premature complexity**

Do **not** add these for the MVP unless a real requirement appears:

| | | |
|---|---|---|
| ❌ Kafka | ❌ RabbitMQ | ❌ Celery |
| ❌ Redis | ❌ Kubernetes | ❌ Complicated AI extraction |
| ❌ Complex search engines | ❌ Microservices | |

**The MVP stack:**

```
React + FastAPI + PostgreSQL + SQLAlchemy + Playwright + APScheduler
```

---

# 7. **CURRENT REPOSITORY**

```
quote-yard/
├── data/                   # RAW scraper output (versioned, never modified)
├── cleaned_data/           # Phase 2A output (gitignored, regenerable)
├── normalized_data/        # Phase 2B output (gitignored, regenerable)
├── branded_data/           # Phase 2C output (gitignored, regenerable)
├── reports/                # Cleaning / brand reports (gitignored, regenerable)
├── data_processing/
│   ├── __init__.py
│   ├── cleaner.py
│   ├── run_cleaning.py
│   ├── normalizer.py
│   ├── run_normalization.py
│   ├── brands.json         # Phase 2C brand list (versioned, hand-made)
│   ├── brand_extractor.py
│   ├── run_branding.py
│   └── taxonomy/           # Phase 2B mapping files (versioned, hand-made)
│       ├── taxonomy.json
│       ├── aliases.json
│       ├── validate_taxonomy.py
│       └── worksheet/
│           └── quote-yard-normalization-mapping-worksheet-filled.csv
├── frontend/
├── scrapers/
├── tests/
│   └── test_brands.py
├── utils/
├── .git/
├── .gitignore
└── .venv/
```

| | |
|---|---|
| **Main MyG scraper** | `scrapers/myg_scraper.py` |
| **Data location** | `data/` |
| **GitHub** | `git@github.com:a1an-mj/Quote-Yard.git` |
| **Main branch** | `main` |

**`.gitignore` must include** all regenerable output: `cleaned_data/`, `normalized_data/`, `normalized_data.tmp/`, `branded_data/`, `branded_data.tmp/`, `reports/` and `*.tar.gz`. (The `.tmp/` directories are staging folders used while a run is in progress.)

---

# 8. **CURRENT MYG SCRAPER**

The MyG scraper uses one configuration dictionary:

```python
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
```

Each category defines: `base_url` · `output` · `label`

**Current selectors:**

```python
PRODUCT_LINK_SELECTOR = "a.line-clamp-2"
PRICE_SELECTOR = '[id^="sec_discounted_price_"]'
AVAILABILITY_SELECTOR = "p.text-green"
```

**Each product becomes:**

```python
{
    "name": "...",
    "price": 39999,
    "url": "...",
    "availability": "In stock",
    "shop": "myG",
    "category": "Mobiles"
}
```

---

# 9. **MYG PRICE CLEANING**

| Raw | Cleaned |
|-----|---------|
| `₹1,23,456.00` | `123456` |

`clean_price()` removes currency symbols, commas and spaces, then converts the value to an integer. **Invalid values become `None`.**

---

# 10. **MYG PAGINATION**

The scraper builds **direct URLs**:

| Page | URL |
|------|-----|
| 1 | `https://www.myg.in/category/` |
| 2 | `https://www.myg.in/category/page-2/` |
| 3 | `https://www.myg.in/category/page-3/` |

It does **not** click pagination buttons. This is intentional, because the site's pagination behavior can differ from direct page navigation.

**Safety limit:** `SAFETY_MAX_PAGES = 100`

---

# 11. **MYG NAVIGATION EDGE CASES**

## 🚧 **403 Forbidden**

Some pages return `403 Forbidden`. Example: `/mobile-phones/page-10/`.

The scraper stops that category cleanly.

> ⚠️ **Suspected data-completeness issue:** in the Phase 2B worksheet, 8 of myG's 11 categories have exactly **108** records (9 pages × 12 products), which matches the page-10 403. These categories are probably **truncated**, not complete. See Section 20, open item 6.

## 🕳️ **404 Not Found**

Some categories have fewer pages. Example: `/home-automation/page-3/` does not exist.

| | |
|---|---|
| **Before the fix** | Scraper waited 10s for `a.line-clamp-2`, hit a `TimeoutError` and crashed. The crash also skipped saving, so products from earlier pages were lost (Home Automation lost 23 products from pages 1–2). |
| **Status** | ✅ **Fixed** |

`scrape_category()` now checks the HTTP response right after `page.goto()`, before the product selector is called:

```python
response = page.goto(url, wait_until="domcontentloaded")

if response and response.status == 404:
    log.warning("Page does not exist (404). Stopping category.")
    break

if response and response.status == 403:
    log.warning("MyG returned 403 Forbidden. Stopping category.")
    break
```

This preserves already-collected products so they can be saved.

> **Fallback (only if needed):** if a missing page ever returns `200` with an empty grid, or redirects instead of a real 404, wrap `page.wait_for_selector()` in `scrape_page()` with a `try/except PlaywrightTimeoutError` that returns an empty list. The existing *"No products found. Stopping category."* check then ends the category cleanly.

---

# 12. **MYG RESOURCE MANAGEMENT**

A major issue encountered: **`ERR_INSUFFICIENT_RESOURCES`**

The page opened normally in Firefox, so the page itself was valid. The likely cause was Chromium resource usage during a long scrape.

## 🛡️ **Current strategy**

**1. Block unnecessary resources**

```python
BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
```

The current JSON does not need these.

**2. Fresh page per category**

```
Browser
   |
Context
   |
   +-- Page -> Mobiles -> close
   +-- Page -> Laptops -> close
   +-- Page -> Tablets -> close
   +-- Page -> Accessories -> close
   +-- Page -> Home & Kitchen -> close
   +-- ...
```

This avoids keeping every category page alive. A new browser per category is **not** required.

---

## 🟦 **12a. OXYGEN DIGITAL SHOP SCRAPER**

**File:** `scrapers/oxygen_scraper.py`

Second retailer scraper, built after MyG stabilized. Same MVP field model as MyG (`name`, `price`, `url`, `availability`, `shop`, `category`). It does not visit product-detail pages or parse RAM/storage from names.

### **Site differences from MyG**

Oxygen runs on **Shopify**, unlike MyG's custom PHP storefront.

| | **MyG** | **Oxygen** |
|---|---------|------------|
| **Selectors** | CSS on visible text (`a.line-clamp-2`, etc.) | `data-*` attributes on the card |
| **Pagination** | `/category/page-2/` | `?page=2` (or `&page=2`) |
| **Price format** | Rupees with ₹ / commas to strip | **Paise** (divide by 100) |

### **Selectors and config**

```python
PRODUCT_CARD_SELECTOR = "div.custom-product-card"
PRODUCT_TITLE_ATTRIBUTE = "data-product-title"
PRODUCT_PRICE_ATTRIBUTE = "data-product-price"
PRODUCT_URL_ATTRIBUTE = "data-product-url"
```

`clean_price()` treats the price attribute as paise (e.g. `1349900` → ₹13,499) and divides by 100.

### **Extra robustness over the MyG scraper**

| Feature | Behavior |
|---------|----------|
| **5xx handling** | Any status `>= 500` stops the category cleanly, not just 403/404 |
| **Per-page try/except** | Logs and breaks cleanly on unexpected errors instead of crashing the run |
| **URL dedup + stop** | Tracks `seen_urls`; a page with zero new URLs stops the category |
| **`detect_availability()`** | Scans card text for "out of stock" / "sold out" / "add to cart"; falls back to checking each button/link |
| **Timing / viewport** | 500ms delay between pages, explicit 1440×900 viewport |

### **Category URLs, verification status**

`CATEGORIES` covers: mobiles, laptops, kitchen-appliances, refrigerators, washing-machines, inverter, battery, gadgets, monitors, printers, led-tv.

- ✅ **mobiles:** the guessed slug `/collections/mobile-phones` was wrong. Correct slug: **`/collections/mobile-smart-phones`**. Confirmed on a real scrape; paise ÷ 100 confirmed (e.g. ₹13,499 Galaxy A07, ₹1,39,999 Galaxy S26 Ultra).
- ✅ **All categories:** a full headless run completed successfully. Pagination (`?page=N`), the URL-dedup stop condition, and every category slug are confirmed end to end.

### **Availability check**

Oxygen's own "Availability" filter on the mobiles collection lists only **"In stock" (58 of 58)**, with no "Out of stock" facet. So the in-stock path is confirmed, but the **out-of-stock path can't be exercised yet**. That is not a scraper gap, just nothing on the site to test against. Revisit if a product goes out of stock, or check a different category.

> ✅ **Status:** Oxygen scraper considered **done for MVP scope**. Same maturity as MyG.

### **Naming inconsistency within Oxygen itself**

| Style | Example |
|-------|---------|
| Most listings | `Samsung Galaxy A07 5G (Black, 128 GB) (6 GB RAM)` |
| Some listings (myG-style pipes) | `realme 16 Pro+ 5G \| 12 GB \| 256 GB \| Master Gold` |

Relevant for normalization/matching: **you can't assume one name format per retailer.**

Likely **duplicate listings** for the same product under slightly different slugs:

```
vivo-v70-fe-northern-lights-purple-8gb-256gb   (name has "2026" suffix)
vivo-v70fe-northern-lights-purple-8gb-256gb    (no "2026", no space in "v70fe")
```

Not a scraper bug, since Oxygen's site has two listings for the same product. URL dedup will not catch these; it is a **Phase 5 product-matching** problem.

### **Oxygen commands**

| Purpose | Command |
|---------|---------|
| All categories | `python scrapers/oxygen_scraper.py` |
| Headless | `python scrapers/oxygen_scraper.py --headless` |
| Selected categories | `python scrapers/oxygen_scraper.py --only mobiles laptops` |
| One category, limited pages | `python scrapers/oxygen_scraper.py --only laptops --max-pages 1` |

---

## 🟨 **12b. PITTAPPILLIL ONLINE STORE SCRAPER**

**File:** `scrapers/pittappillil_scraper.py`

Third retailer scraper. Same MVP field model (`name`, `price`, `url`, `availability`, `shop`), plus a second classification field unique to this retailer so far: **`subcategory`**.

### **Selectors and config**

```python
PRODUCT_CARD_SELECTOR = ".products-list__item"
PRODUCT_NAME_SELECTOR = ".product-card__name a"
PRICE_SELECTOR = ".product-card__prices"
AVAILABILITY_SELECTOR = ".product-card__availability span"
```

### **The tricky part: price extraction**

The price block holds both the current price and a struck-through original price:

```html
<div class="product-card__prices">
    ₹ 35999
    <small><strike>₹ 58999</strike></small>
</div>
```

`extract_current_price()` reads only the **direct text node** (skipping nested `<small>` / `<strike>`), so the discounted price is captured and the original is ignored.

**Pagination** uses query parameters:

```
/stores/Mobile
/stores/Mobile?page=2&limit=12
```

**Defensive posture (same as Oxygen):** 403/404/5xx stop the category cleanly · `seen_urls` dedup with "no new products" stop · fresh browser context per subcategory · image/media/font blocking.

### **Category structure: category + subcategory**

Pittappillil exposes ~55 store pages. One JSON file per page would mean 55 small ungrouped files. Instead, `CATEGORIES` is **two levels deep**:

```python
CATEGORIES = {
    "kitchen-appliances": {
        "label": "Kitchen Appliances",
        "output": "pittappillil_kitchen_appliances.json",
        "subcategories": {
            "air-fryer": {"url": "...", "label": "Air Fryer"},
            "appachatty": {"url": "...", "label": "Appachatty"},
            ...
        },
    },
    "home-appliances": {...},
    "home-audio": {...},
    "air-quality": {...},
    "mobiles-laptops": {...},
}
```

Each product is tagged with both fields:

```python
{
    "name": "Philips Air Fryer...",
    "price": 8999,
    "url": "https://www.pittappillilonline.com/...",
    "availability": "In stock",
    "shop": "Pittappillil",
    "category": "Kitchen Appliances",
    "subcategory": "Air Fryer"
}
```

**5 main categories · 55 subcategories**

| Main category | Subcategories | Output file |
|---------------|:-------------:|-------------|
| Kitchen Appliances | 36 | `pittappillil_kitchen_appliances.json` |
| Home Appliances | 8 | `pittappillil_home_appliances.json` |
| Home Audio | 2 | `pittappillil_home_audio.json` |
| Air Quality and Circulation | 5 | `pittappillil_air_quality.json` |
| Mobiles, Laptops and More | 4 | `pittappillil_mobiles_laptops.json` |

This gives **5 files instead of 55**, while keeping the subcategory on every product. It maps directly onto the category → subcategory hierarchy planned for PostgreSQL.

### **Pittappillil CLI**

`--only` selects **main categories**; `--subcategories` narrows further.

| Purpose | Command |
|---------|---------|
| All categories | `python scrapers/pittappillil_scraper.py` |
| Headless | `python scrapers/pittappillil_scraper.py --headless` |
| Selected main categories | `python scrapers/pittappillil_scraper.py --only kitchen-appliances home-appliances` |
| Spot-check one subcategory | `python scrapers/pittappillil_scraper.py --only mobiles-laptops --subcategories mobiles --max-pages 1` |

> ✅ **Status:** built, restructured, and confirmed running.
>
> ⚠️ **Open item:** the 55 subcategory URLs have not been individually spot-checked. The Phase 2B worksheet found only **48** distinct Pittappillil subcategories with products, so about 7 configured subcategories returned nothing. See Section 20, open item 4.

---

# 13. **MYG SCRAPER COMMANDS**

| Purpose | Command |
|---------|---------|
| All categories | `python scrapers/myg_scraper.py` |
| Headless | `python scrapers/myg_scraper.py --headless` |
| Selected categories | `python scrapers/myg_scraper.py --only mobiles tablets` |
| One category | `python scrapers/myg_scraper.py --only home-automation` |
| Page safety limit | `python scrapers/myg_scraper.py --max-pages 20` |

---

# 14. **EXISTING MYG WORK**

## 📱 **Mobiles**

Previously collected ~**108 products** before hitting a 403 at page 10.

Parsing extracted **RAM, Storage, Color**. Some feature phones legitimately had no normal RAM field.

> 💡 **Important discovery:** product names and URLs can disagree on variants / colors / storage. The **displayed product name** is more trustworthy for variant info than deriving it from URLs.

Mobile data is considered **good enough for now** (but see the 108-record truncation note in Section 11).

## 💻 **Laptops**

Names were inconsistent, especially Apple products, gaming laptops and desktop/AIO listings. The processor parser was improved and tested with:

| | |
|---|---|
| AMD Ryzen 7 | AMD Ryzen 5 |
| Intel Core i3 | Intel Core i5 |
| Intel Core Ultra 5 225H | M5 Pro Chip |
| Intel Core i7 14700HX | AMD Ryzen 7 7735HS |

Laptop parsing is considered **good enough for now**.

## 📲 **Tablets · 📺 TVs · 🎧 Accessories**

Use the simple listing approach:

```python
name = product["name"].split("|")[0].strip()
```

Keep: `name` · `price` · `url` · `availability` · `shop` · `category`

Duplicate listings and missing availability were observed, and are **not** being over-engineered yet.

---

# 15. **PRODUCT PARSING STRATEGY GOING FORWARD**

For new categories, **do not over-parse specifications.**

```
Raw listing -> name, price, url, availability, shop, category
```

Only add category-specific parsing when there is a **real requirement**. This keeps inconsistent retailer naming from making the project needlessly complicated.

---

# 16. **JSON SAVING**

Saving **replaces** the existing JSON snapshot. It does **not** append.

| | Contents |
|---|----------|
| Old | Phone A, Phone B |
| New scrape | Phone A, Phone C |
| **Result** | **Phone A, Phone C** |

This is intentional for the current snapshot stage. Later, PostgreSQL will store price history separately.

---

# 17. **DEBUGGING RULE**

Always debug in this order:

```
Fix 1
  |
Test once
  |
If broken -> Fix 2
  |
Test once
  |
If still broken -> Fix 1 + Fix 2
  |
Test once
```

> Do **not** change multiple unrelated things before testing. Use **one test per change**, so it's clear what actually solved the issue.

---

# 18. **DEVELOPMENT ENVIRONMENT**

| | |
|---|---|
| **OS** | Arch Linux |
| **Python** | 3.14.6 |
| **Environment** | `.venv` |
| **Tools** | Playwright, Chromium |

Playwright reported Arch Linux is not officially supported and downloaded a fallback Ubuntu 24.04 Chromium build, but the browser works.

> 🐛 A previous file named `inspect.py` shadowed Python's standard-library `inspect` module. It was renamed to **`inspect_page.py`**.

---

# 19. **IMPLEMENTATION ROADMAP**

## **Phase 1: Data Collection** ✅

```
MyG (stable)
   |
Oxygen (done, all categories verified)
   |
Pittappillil (done, category/subcategory grouping, confirmed working)
   |
Nandilath G Mart (done, built and full-page tested)
```

Four active retailers are available for the core pipeline. **Croma is intentionally deferred** and can be added later using the same retailer-specific scraper interface.

## **Phases 2 to 8**

| Phase | Name | What gets built |
|:-----:|------|-----------------|
| **2** | **Data Processing** | 2A Cleaning ✅ · 2B Normalization ✅ (built, reviewed, verified) · Duplicate handling ✅ decided (DB) · 2C Brand extraction 🚧 built, first run and review pending |
| **3** | **PostgreSQL** | Schema, SQLAlchemy models, retailer records, product records, listings, prices, price history |
| **4** | **FastAPI** | Product endpoints, search, product detail, comparison, price history |
| **5** | **Product Matching** | Match retailer listings into canonical products |
| **6** | **React Integration** | Connect frontend to FastAPI |
| **7** | **Scheduler** | Automate retailer scraping and DB updates |
| **8** | **Deployment** | Choose environment, move from development to a stable server |

---

## 🧹 **19a. PHASE 2A: DATA CLEANING** ✅

Cleaning is deliberately separate from normalization. It validates and tidies records but never changes their meaning.

**Pipeline:** `data/*.json` → `cleaner.py` → `cleaned_data/*.json` + `reports/cleaning_report.json`

**Run:** `python data_processing/run_cleaning.py`

### Cleaning rules

- Validate required fields: name, price, url, availability, shop, category
- Trim and collapse whitespace
- Require a positive integer price
- Validate http/https URLs
- Missing availability becomes `"Unknown"` (never "Out of stock")
- Preserve `subcategory: null` (no inventing subcategories from product names)
- Preserve original product names (no aggressive rewriting)
- Preserve duplicate URLs and flag them in the report
- Do not normalize categories or subcategories (that is Phase 2B)

### Baseline results (first full run)

| Metric | Value |
|--------|------:|
| Files processed | 38 |
| Input records | 2,975 |
| Cleaned records | 2,975 |
| Removed records | 0 |
| Validation errors | 0 |
| Availability: In stock | 2,796 |
| Availability: Unknown | 179 (mostly myG) |
| Duplicate URL groups | 10 (20 records) |

| Retailer | Files | Records |
|----------|------:|--------:|
| myG | 11 | 1,103 |
| Nandilath G Mart | 11 | 749 |
| Oxygen | 11 | 245 |
| Pittappillil | 5 | 878 |

### Key findings from the audit

- **Subcategory is inconsistent:** myG (1,103) and Oxygen (245) have none; Nandilath and Pittappillil have them (1,627 records total).
- **Availability `None` means the scraper could not tell**, not out of stock.
- **Duplicate URLs are mostly Nandilath products listed under several subcategories** (e.g. a soundbar under Home Theater and Sound Bars). Dedupe by URL would lose category data. The DB design must allow one listing to belong to multiple categories.
- **Category names vary across and within retailers** (Mobiles / Mobiles & Laptops, TV / LED TV, Printer / Printers, Gas stove / Gas Stove, Dishwasher / Dish Washer, Home Theatre / Home Theater). Handled in Phase 2B.

### Repo rules

- `data/` is the raw snapshot: never modified by processing code.
- `cleaned_data/`, `normalized_data/`, `branded_data/`, `reports/` and `*.tar.gz` are gitignored because they are regenerable or too large.

### Known gap

The validator has never failed on real data (0 errors across 2,975 records). Confirm it is strict enough to ever reject something, and add per-category price **warnings** (not errors) to the cleaning report. A flat ceiling would wrongly flag legitimate MacBooks, large TVs and premium ACs.

---

## 🗂️ **19b. PHASE 2B: NORMALIZATION** ✅

Normalization maps each retailer's own category names onto **Quote Yard's canonical taxonomy**. The database must never depend on retailer category names.

```
cleaned listing
   ↓
(retailer, raw_category, raw_subcategory)
   ↓
aliases.json  →  canonical product type
   ↓
taxonomy.json →  canonical parent category
   ↓
brand extraction (Phase 2C)
   ↓
product matching (Phase 5)
```

**Pipeline:** `cleaned_data/*.json` → `normalizer.py` → `normalized_data/*.json`

### Design decisions

- **Mapping key is the full tuple** `(retailer, raw_category, raw_subcategory)`, not category alone. Retailer categories are navigation, not product type (e.g. Pittappillil's "Mobiles, Laptops and More" holds phones, laptops and watches).
- **Product type first, parent derived.** A type like `Air Fryer` belongs to exactly one parent (`Kitchen Appliances`). Type names are globally unique, so the parent is always looked up from the type.
- **Null subcategory** uses the sentinel key `__none__`. Fallback order: full tuple, then unmapped. Retailers that give a real subcategory (Nandilath "Laptop", "Printer") use that real value as the key.
- **Explicit mappings only.** No heuristics such as `.lower().rstrip("s")`. Lookup keys are casefolded, so capitalization variants (`Gas stove` / `Gas Stove`) do not need separate entries.
- **Mapping status per row:**
  - `mapped`: category tells us the exact product type
  - `parent_only`: broad parent known, product type unknown (`product_type = null`)
  - `unmapped`: bucket too mixed to label; reported, never guessed
- **One type per big appliance.** `Refrigerator`, `Washing Machine`, `Television` and `Mobile Phone` are single types. Door style, load type and smart/non-smart become attributes later. Genuinely different products stay separate (Washer Dryer, Clothes Dryer, Chest Freezer, Commercial Refrigerator, Air Cooler, and each fan type).
- **Odd non-appliance items** (Cookware, Casserole, Pressure Cooker, Biriyani Pot, Ironing Board, Cloth Dryer stand, Barbeque, Emergency Light) map to `Other Kitchen & Home Item`.
- **No inventing subcategories** for myG and Oxygen. Name-based classification, if ever done, is a separate, versioned rule layer.

> **MVP decision (unmapped coverage):** 80% of records (2,389 of 2,975) are fully mapped. The remaining 20% (346 `parent_only`, 240 `unmapped`) **pass through unchanged** for the MVP. Causes: mixed retailer buckets (myG Home & Kitchen, myG Small Appliances, Oxygen Gadgets, Pittappillil Chimney & Hob, Home Inverters & Batteries) and one misfiled Nandilath record. A name-based rule layer (`mapping_status: "rule_mapped"`, versioned separately) is **deferred**. Cheap wins later: an `Earbuds` type would let Oxygen Gadgets (23) map.

> **Decision (duplicate handling):** `normalized_data/` **keeps every record**, including repeated URLs. Normalization stays a pure per-record transform. The Phase 3 loader creates **one listing per `(shop, url)`** and **one row in a listing ↔ category join table for each distinct `(category, product_type)`** seen for that URL.

### Files (`data_processing/taxonomy/`)

| File | Purpose |
|------|---------|
| `taxonomy.json` | Canonical taxonomy v1.0: 14 parent categories, 48 product types |
| `aliases.json` | Retailer tuple → status + product type (113 keys, all observed combinations). Stores `taxonomy_version`. |
| `validate_taxonomy.py` | Checks types are unique and exist, statuses are consistent, and (given `cleaned_data/`) every observed tuple has a mapping |
| `worksheet/…-filled.csv` | Snapshot of the review worksheet the JSON was generated from. **The JSON is the source of truth; the CSV is not regenerated.** |

**Run before every normalization:** `python data_processing/taxonomy/validate_taxonomy.py cleaned_data`

### Worksheet results

| Status | Rows | Records |
|--------|-----:|--------:|
| mapped | 102 | 2,389 (80%) |
| parent_only | 7 | 346 |
| unmapped | 4 | 240 |
| **Total** | **113** | **2,975** |

`parent_only`: myG Accessories, Personal Care, Home Automation; Oxygen Kitchen Appliances; Pittappillil Chimney & Hob, Home Inverters & Batteries, Mobile Accessories.
`unmapped`: myG Home & Kitchen, myG Small Appliances, Oxygen Gadgets, Nandilath "Mobiles & Laptops → Accessories" (misfiled; the sample is a refrigerator).

### Normalized record

```json
{
  "name": "Samsung ...",
  "price": 42999,
  "url": "https://...",
  "availability": "In stock",
  "shop": "Nandilath G Mart",

  "raw_category": "Home Audio",
  "raw_subcategory": "Sound Bars",

  "category": "Home Audio",
  "product_type": "Soundbar",
  "mapping_status": "mapped",
  "taxonomy_version": "1.0"
}
```

Raw values are kept next to canonical ones, so a wrong mapping can be redone **without re-scraping**.

### Guardrails for `normalizer.py`

1. **Unmapped-tuple detection:** a new retailer/category combination must never silently fall through. Fail or report it.
2. **Determinism / idempotency:** the normalizer reads `raw_*` fields only; the same cleaned input always gives the same output, and re-running on normalized output changes nothing.
3. **Coverage in both directions:** every observed tuple has a key, and every key is used (the validator warns on unused keys).
4. **Version both files:** bump `version` in `taxonomy.json` and `taxonomy_version` in `aliases.json` together when a mapping changes.

### Rows reviewed

- Nandilath **Cooktop** (25)
- Pittappillil **Mixer Grinders** (78)
- Pittappillil **Chimney & Hob** (54)
- Pittappillil **Home Inverters & Batteries** (12)

### Review results

**No mapping changes were needed, so the taxonomy version stays at 1.0.**

| Row | Finding |
|-----|---------|
| Nandilath **Cooktop** (25) | Gas burner units, with about 4 possibly hobs. Stays mapped to Gas Stove. |
| Pittappillil **Mixer Grinders** (78) | Clean. |
| Pittappillil **Chimney & Hob** (54) | About 32 chimneys and 22 hobs. Stays `parent_only`; names could split it later. |
| Pittappillil **Home Inverters & Batteries** (12) | 7 inverters and 5 batteries. Stays `parent_only`; names could split it later. |

**Type coverage:** 30 of 48 types have 2+ retailers (18 have one). Chimney and Hob show as Nandilath-only because Pittappillil's records are `parent_only`. Tablet is myG-only (108 records, likely truncated).

---

## 🏷️ **19c. PHASE 2C: BRAND EXTRACTION** 🚧

Adds `brand` and `brand_status` to each normalized record. Brand extraction is a separate step: it never changes category, product type or name, and it is not product matching.

**Pipeline:** `normalized_data/*.json` → `brand_extractor.py` → `branded_data/*.json` + `reports/brand_report.json`

### Added fields

| Field | Values |
|-------|--------|
| `brand` | Canonical brand name from `brands.json`, or `null` |
| `brand_status` | `matched` or `unknown` |

```json
{
  "name": "Samsung Galaxy S25 5G | 12 GB | 256 GB",
  "shop": "myG",
  "category": "Mobiles & Tablets",
  "product_type": "Mobile Phone",
  "mapping_status": "mapped",
  "taxonomy_version": "1.0",

  "brand": "Samsung",
  "brand_status": "matched"
}
```

### Design decisions

- **Explicit list, no guessing.** `brands.json` maps each canonical brand name to its aliases. A name with no matching alias gets `brand: null`, `brand_status: "unknown"`, and is listed in the report.
- **Whole-token matching** on the casefolded name with punctuation removed. An alias never matches inside another word.
- **Earliest match in the name wins**, and the **longest alias wins ties** at the same position.
- **Ambiguous aliases are `start_only`.** `HP`, `Nothing` and `Vu` only match at the start of the name, because names contain "1.5 HP" (air conditioner capacity) and ordinary words like "nothing".
- **Sub-brands stay separate.** Redmi is not merged into Xiaomi until product matching needs otherwise.
- **Read-only on everything else.** All existing fields pass through unchanged, and the same input always gives the same output.

### Files

| File | Purpose |
|------|---------|
| `data_processing/brands.json` | Canonical brand → aliases (versioned, hand-made) |
| `data_processing/brand_extractor.py` | Matching logic |
| `data_processing/run_branding.py` | Runner: reads `normalized_data/`, writes `branded_data/` and `reports/brand_report.json` |
| `tests/test_brands.py` | Tests for token matching, earliest/longest rules and `start_only` aliases |

### Run

```
python data_processing/run_branding.py
python -m pytest tests/test_brands.py
```

### Status

Built. **First run and review are pending.** The loop is: run, read the unknown brands in `reports/brand_report.json`, add them to `brands.json`, rerun, until the unknown count is small.

---

# 20. **CURRENT STATUS**

## ✅ **Completed / substantially completed**

**General**

| | |
|---|---|
| Quote Yard concept | Technology direction |
| Repository setup | Git / GitHub setup |
| Frontend prototype direction | System Requirements + SRS spreadsheet |

**Data Cleaning (Phase 2A):** built, run and verified

- Generic cleaner works on the common listing model (no retailer-specific logic)
- 2,975 / 2,975 records passed, 0 validation errors
- Availability standardized (2,796 In stock, 179 Unknown)
- 10 duplicate URL groups flagged, not removed
- Cleaning report written to `reports/cleaning_report.json`

**Normalization (Phase 2B):** built, reviewed, verified

- Category and subcategory audit complete (27 category names, 85 subcategory values)
- Mapping worksheet: 113 unique `(retailer, category, subcategory)` combinations, all classified
- `taxonomy.json` v1.0 (14 categories, 48 product types) and `aliases.json` generated; `validate_taxonomy.py` passes
- `normalizer.py` and `run_normalization.py` built; output in `normalized_data/`
- Review of the four flagged rows complete; **no mapping changes needed, version stays 1.0**
- **MVP decision:** 80% of records fully mapped; `parent_only` (346) and `unmapped` (240) pass through unchanged; rule-based layer deferred
- **Duplicate handling decided:** `normalized_data/` keeps repeated URLs; the Phase 3 loader builds one listing per `(shop, url)` plus a listing ↔ category join table

**MyG**

| | |
|---|---|
| Scraping architecture | Mobile scraping |
| Laptop scraping | Tablet scraping |
| TV scraping | Accessories pipeline |
| Basic Home & Kitchen scraping | Resource blocking |
| Fresh page per category | 403 handling |
| 404 handling | Simple raw-listing strategy |

**Oxygen**: built and fully verified

- 5xx handling · per-page error handling · URL deduplication
- Availability detection · all category URLs verified
- Pagination verified · price conversion verified

**Pittappillil**: built and confirmed running

- 403/404/5xx handling · per-page error handling · URL deduplication
- Category/subcategory grouping (5 main / 55 configured sub)
- Grouped JSON output · category and subcategory on every product

**Nandilath G Mart**: built and confirmed

- WordPress / WooCommerce storefront inspected
- Uses `.wd-product` cards, names/URLs from `.wd-entities-title a`, the discounted `<ins>` price when present, and `/page/N/` pagination
- Card selectors, name/URL, current/discounted price, availability confirmed
- Category/subcategory grouping · `/page/N/` pagination confirmed
- Full-page testing completed · duplicate URL protection
- Resource blocking · 403/404/5xx handling

> **Four retailers are active:** myG · Oxygen · Pittappillil · Nandilath G Mart
>
> **Croma is deferred.** The architecture must stay retailer-scalable so it can be added without changing the core normalization, database, backend or frontend design.

## 🚧 **Currently being finished**

**Brand extraction (Phase 2C):** built (`brands.json`, `brand_extractor.py`, `run_branding.py`, `tests/test_brands.py`). First run and review of unknown brands pending.

**MyG scraper robustness** (parallel track): confirm the unified MyG scraper is robust end to end against:

| | |
|---|---|
| 403 | 404 *(fix applied; confirming run may still be needed)* |
| Resource exhaustion | Categories with different page counts |
| Missing availability | Navigation failures |

## 🔎 **Open items to verify**

| # | Item |
|:-:|------|
| 1 | **MyG TVs:** the cleaned data contains a myG `TV` category (108 records), but `CATEGORIES` in `myg_scraper.py` has no `tvs` entry. Confirm whether an earlier script scraped them or whether the config needs updating, so a re-scrape does not lose them. |
| 2 | **Oxygen naming:** listings are internally inconsistent and may contain near-duplicates (a Phase 5 matching problem). |
| 3 | **Oxygen out-of-stock path:** unverified, because the tested category had no out-of-stock products. |
| 4 | **Pittappillil subcategories:** 55 URLs are configured but only 48 subcategories appear in the data. Find which 7 returned nothing and confirm that is expected, not a silent scraper stop. |
| 5 | ~~**Run the validator on real data**~~ ✅ Done as part of the Phase 2B verification. |
| 6 | **myG truncation:** 8 of 11 myG categories have exactly 108 records, matching the page-10 403. These are probably incomplete, which affects price-comparison coverage (Tablet is myG-only, so its coverage is affected most). Investigate whether the 403 can be avoided (delays, headers, a new context per page range). Runs as a parallel track. |
| 7 | **Unknown brands:** after the first `run_branding.py` run, review `reports/brand_report.json` and add missing brands to `brands.json`. |

## ➡️ **Next major work**

The four scrapers are now the data-collection layer. **Do not add Croma yet.**

```
Four retailer raw data -> Data Cleaning -> Normalization -> Brand Extraction -> PostgreSQL
```

The architecture must stay scalable so future retailers plug into the same common listing model **without retailer-specific logic leaking into later phases.**

---

# 21. **HARDEST PARTS**

| Area | Why it's hard |
|------|---------------|
| 🔗 **Product matching** | Deciding whether different retailer listings are the same product / variant |
| 🕷️ **Reliable multi-retailer scraping** | Every retailer differs in HTML, pagination, price format, availability and anti-bot behavior |
| 🗄️ **Database design** | Supporting canonical products, listings, variants, current prices and historical prices |
| 🧼 **Data quality** | Duplicates, missing values, inconsistent names, changed URLs, temporary failures |
| 🤖 **Automation** | Letting one retailer fail without stopping the entire update |

---

# 22. **WHAT QUOTE YARD SHOULD EVENTUALLY DO**

```
Retailer Websites -> Scrapers -> Data Normalization -> Brand Extraction -> Product Matching
-> PostgreSQL -> FastAPI -> React -> User Search -> Price Comparison
```

## 🎯 **Example final experience**

User searches: **"Samsung Galaxy S25"**

Quote Yard finds the relevant product:

**Samsung Galaxy S25 256GB**

| Retailer | Price |
|----------|-------|
| myG | ₹39,999 |
| Oxygen | ₹40,499 |
| Pittappillil | ₹40,999 |
| Croma | ₹41,999 |

…along with **price history · availability · retailer links · product details**.

> The goal: build a **working end-to-end price comparison system first**, then progressively improve matching, data quality, automation and UX.

---

# 23. **IMMEDIATE NEXT STEP**

## ➡️ **Phase 2C: run and review brand extraction**

Phases 2A and 2B are done (Sections 19a and 19b). Brand extraction is built (Section 19c); start from `normalized_data/`.

Order of work:

1. **Run:** `python data_processing/run_branding.py`
2. **Review the unknown brands** in `reports/brand_report.json` and add them to `data_processing/brands.json` (aliases explicit and reviewable; ambiguous ones `start_only`)
3. **Rerun** until the unknown count is small
4. **Tests:** `python -m pytest tests/test_brands.py`
5. **Phase 3: PostgreSQL.** Schema, SQLAlchemy models, and a loader that creates one listing per `(shop, url)` plus a listing ↔ category join row per distinct `(category, product_type)`
6. **Product matching** (Phase 5, kept separate)

**Parallel track:** the myG truncation (Section 20, open item 6).

Rules: mappings and brand aliases are explicit and reviewable (JSON files, not heuristics); unknown values are reported, never silently guessed; raw, cleaned and normalized layers stay untouched; `taxonomy.json` and `aliases.json` are versioned together.
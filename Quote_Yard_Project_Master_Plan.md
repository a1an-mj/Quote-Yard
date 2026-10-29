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
| 11 | [MyG Edge Cases](#11-myg-navigation-edge-cases) | 19d | [Phase 3: PostgreSQL](#19d-phase-3-postgresql-) |
| 12 | [Resource Mgmt / Oxygen / Pittappillil](#12-myg-resource-management) | 19e | [Phase 4: FastAPI](#19e-phase-4-fastapi-) |
| | | 20 | [Current Status](#20-current-status) |
| | | 21 | [Hardest Parts](#21-hardest-parts) |
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
PostgreSQL loader (Phase 3)       <- done
   |
   v
FastAPI (Phase 4)                 <- done
   |
   v
Product Matching (Phase 5)        <- next
   |
   v
Accounts + watchlist (Phase 4A)   <- after Phase 5
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

> Product matching stays **separate** from scraping, from normalization and from brand extraction. Matching must treat `brand_status: "review"` (and `unknown`) as "brand not trustworthy".

## 🗄️ **3.4 Database**

| | |
|---|---|
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy 2 (psycopg 3 driver) |

```
Canonical Product
   |
   +---- myG listing
   +---- Oxygen listing
   +---- Pittappillil listing
   +---- Nandilath G Mart listing
   +---- Croma listing
```

The Phase 3 schema is built and loaded: `retailers`, `listings`, `listing_categories`, `price_history` and an empty `canonical_products` table reserved for Phase 5. See [Section 19d](#19d-phase-3-postgresql-).

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

The built Phase 4 endpoints (listings-based, since canonical products do not exist yet) are in [Section 19e](#19e-phase-4-fastapi-).

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
Landing (1-2 featured deals, no search bar) -> click a deal -> Sign Up / Login
   -> Dashboard (search, filters, listings, per-retailer comparison, watchlist, account)
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
| **Backend** | Python, FastAPI, SQLAlchemy 2 |
| **Database** | PostgreSQL (driver: psycopg 3) |
| **Scraping** | Python, Playwright, Chromium |
| **Scheduling** | APScheduler |
| **Development** | Git, GitHub, pytest |

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
├── reports/                # Cleaning / normalization / brand reports (gitignored, regenerable)
├── data_processing/
│   ├── __init__.py
│   ├── cleaner.py
│   ├── run_cleaning.py
│   ├── normalizer.py
│   ├── run_normalization.py
│   ├── review_normalized.py    # read-only review report over normalized_data/
│   ├── brands.json             # Phase 2C brand list (versioned, hand-made)
│   ├── brand_extractor.py
│   ├── run_branding.py
│   └── taxonomy/           # Phase 2B mapping files (versioned, hand-made)
│       ├── taxonomy.json
│       ├── aliases.json
│       ├── validate_taxonomy.py
│       └── worksheet/
│           └── quote-yard-normalization-mapping-worksheet-filled.csv
├── db/                     # Phase 3: database layer
│   ├── __init__.py
│   ├── session.py          # engine / connection URL
│   ├── models.py           # SQLAlchemy models and constraints
│   ├── create_tables.py    # create tables + seed the four retailers
│   └── loader.py           # branded_data/ -> PostgreSQL
├── api/                    # Phase 4: read-only HTTP API (FastAPI)
│   ├── __init__.py
│   ├── main.py             # app, /api/v1 prefix, CORS, rate limiting
│   ├── deps.py             # read-only engine (statement timeout) + session dependency
│   ├── schemas.py          # Pydantic response models
│   ├── filters.py          # shared listing filters (EXISTS-based, escaped search)
│   ├── ratelimit.py        # in-process sliding-window rate limiter
│   └── routes/
│       ├── __init__.py
│       ├── health.py
│       ├── catalog.py      # retailers, product types, brands
│       └── listings.py     # list, summary, detail, prices
├── frontend/
├── scrapers/
├── tests/
│   ├── conftest.py              # switches the rate limiter off for the shared test app
│   ├── test_normalizer.py
│   ├── test_brands.py
│   ├── test_db_models.py
│   ├── test_loader.py
│   ├── test_api_health.py
│   ├── test_api_catalog.py
│   ├── test_api_listings.py
│   ├── test_api_summary_detail.py
│   └── test_api_ratelimit.py
├── utils/
├── requirements.txt
├── requirements-dev.txt
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

> **Check:** a recent sketch of the repo showed `scrapers/` as folders (`myg/`, `oxygen/`, ...) while Sections 8 to 13 describe single files such as `scrapers/myg_scraper.py`. Confirm the real layout and update the commands in Sections 12 and 13 if the scrapers were reorganized.

**`.gitignore` must include** all regenerable output: `cleaned_data/`, `normalized_data/`, `normalized_data.tmp/`, `branded_data/`, `branded_data.tmp/`, `reports/`, `*.tar.gz` and `.venv/`. (The `.tmp/` directories are staging folders used while a run is in progress.)

**Import / run style:**
- `data_processing/` runners use `from normalizer import ...` and `from brand_extractor import ...`, so run them **by path**: `python data_processing/run_normalization.py`. The tests add `data_processing/` to `sys.path`.
- The `db/` package uses package imports, so run it **as a module from the repo root**: `python -m db.create_tables`, `python -m db.loader`.

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

> ⚠️ **Confirmed data-completeness issue:** 8 of myG's 11 categories have exactly **108** records (9 pages × 12 products), which matches the page-10 403. The Phase 2B normalized output shows the same counts. These categories are probably **truncated**, not complete. See Section 20, open item 6.

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

This gives **5 files instead of 55**, while keeping the subcategory on every product. It maps directly onto the category → subcategory hierarchy used in PostgreSQL.

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

This is intentional for the JSON snapshot stage. Price history is kept in PostgreSQL (`price_history`), built up by the loader on every run.

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
| **Database** | PostgreSQL, local database `quote_yard` (Unix-socket connection as the current OS user) |
| **Tools** | Playwright, Chromium |
| **Dev tools** | pytest (run as `python -m pytest`), httpx2 (the API test client; Starlette prefers it over httpx) |

**Setup on a fresh machine:**

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium        # the browser is downloaded separately; only the scrapers need it
createdb quote_yard
python -m db.create_tables
```

**Requirements files:** `requirements.txt` (runtime: playwright, SQLAlchemy, psycopg[binary], fastapi, uvicorn) and `requirements-dev.txt` (adds pytest and httpx2). Phase 4A adds an argon2 password-hashing package (or uses the standard-library `scrypt`) and sends email through SMTP (standard-library `smtplib`); APScheduler arrives in Phase 7.

**Run the API:** `uvicorn api.main:app --reload`, then open `http://127.0.0.1:8000/api/v1/docs`. **Run all tests:** `python -m pytest tests -q` (103 pass).

**Database URL:** read from the environment variable `QUOTE_YARD_DATABASE_URL`; the default is `postgresql+psycopg:///quote_yard`.

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
| **2** | **Data Processing** ✅ | 2A Cleaning ✅ · 2B Normalization ✅ · 2C Brand extraction ✅ (98.9% matched, 10 `review`, 23 unknown) · Duplicate handling ✅ (done in the loader) |
| **3** | **PostgreSQL** ✅ | Schema, SQLAlchemy models, retailers seeded, loader, price history. 2,965 listings loaded; reruns are idempotent. |
| **4** | **FastAPI foundation + basic protection** ✅ | `/api/v1` read-only API: listing search and filters, per-retailer summary, listing detail, price history, browse by product type / brand. Read-only DB connection, statement timeout, pagination caps, CORS, rate limiting. 62 API tests. |
| **5** | **Product Matching** ⏳ next | Match retailer listings into canonical products (fills `canonical_products`), starting with mobile phones: a read-only extraction report first, then conservative matching (brand, model, RAM and storage must agree; ambiguous cases go to a review report). Then `/products` and `/compare` endpoints. |
| **4A** | **Accounts, watchlist and public deal teaser** (after Phase 5) | Open registration with **email verification by OTP**, token-based sessions (opaque token in an httpOnly cookie), secure password hashing, abuse protection; the full platform requires login; personal watchlist; public landing page with 1-2 verified deals generated from real matches (no search bar); dashboard. About six days including email verification. |
| **6** | **React Integration** | Connect frontend to FastAPI |
| **7** | **Scheduler** | Automate retailer scraping and DB updates (scrape → clean → normalize → brand → load) |
| **8** | **Deployment** | Choose environment, move from development to a stable server |
| **9** | **Vendor accounts and local shop deals** (future, not in the current sprint) | Vendor registration and review, weekly offers with validity periods, stored separately from scraped data and linked to canonical products; verified vendors, scraped listings and vendor offers shown distinctly. See Section 23. |

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
- **Duplicate URLs are all Nandilath products listed under several subcategories** (e.g. a soundbar under Home Theater and Sound Bars; confirmed after loading: 749 Nandilath records became 739 listings, the other retailers have none). Dedupe by URL would lose category data. The DB design must allow one listing to belong to multiple categories.
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

**Pipeline:** `cleaned_data/*.json` → `normalizer.py` → `normalized_data/*.json` + `reports/normalization_report.json`

### Design decisions

- **Mapping key is the full tuple** `(retailer, raw_category, raw_subcategory)`, not category alone. Retailer categories are navigation, not product type (e.g. Pittappillil's "Mobiles, Laptops and More" holds phones, laptops and watches).
- **Product type first, parent derived.** A type like `Air Fryer` belongs to exactly one parent (`Kitchen Appliances`). Type names are globally unique, so the parent is always looked up from the type.
- **Null subcategory** uses the sentinel key `__none__`. Retailers that give a real subcategory (Nandilath "Laptop", "Printer") use that real value as the key.
- **Explicit mappings only.** No heuristics such as `.lower().rstrip("s")`. Lookup keys are casefolded, so capitalization variants (`Gas stove` / `Gas Stove`) do not need separate entries.
- **Mapping status per row:**
  - `mapped`: category tells us the exact product type
  - `parent_only`: broad parent known, product type unknown (`product_type = null`)
  - `unmapped`: bucket too mixed to label; reported, never guessed
- **One type per big appliance.** `Refrigerator`, `Washing Machine`, `Television` and `Mobile Phone` are single types. Door style, load type and smart/non-smart become attributes later. Genuinely different products stay separate (Washer Dryer, Clothes Dryer, Chest Freezer, Commercial Refrigerator, Air Cooler, and each fan type).
- **Odd non-appliance items** (Cookware, Casserole, Pressure Cooker, Biriyani Pot, Ironing Board, Cloth Dryer stand, Barbeque, Emergency Light) map to `Other Kitchen & Home Item`.
- **No inventing subcategories** for myG and Oxygen. Name-based classification, if ever done, is a separate, versioned rule layer.

> **MVP decision (unmapped coverage):** 80% of records (2,389 of 2,975) are fully mapped. The remaining 20% (346 `parent_only`, 240 `unmapped`) **pass through unchanged** for the MVP. Causes: mixed retailer buckets (myG Home & Kitchen, myG Small Appliances, Oxygen Gadgets, Pittappillil Chimney & Hob, Home Inverters & Batteries) and one misfiled Nandilath record. A name-based rule layer (`mapping_status: "rule_mapped"`, versioned separately) is **deferred**. Cheap wins later: an `Earbuds` type would let Oxygen Gadgets (23) map.

> **Decision (duplicate handling):** `normalized_data/` **keeps every record**, including repeated URLs. Normalization stays a pure per-record transform. The Phase 3 loader creates **one listing per `(shop, url)`** and **one row in `listing_categories` per distinct raw category pair** seen for that URL. ✅ Implemented in Phase 3.

### Files

| File | Purpose |
|------|---------|
| `taxonomy/taxonomy.json` | Canonical taxonomy v1.0: 14 parent categories, 48 product types |
| `taxonomy/aliases.json` | Nested `mappings[shop][category][subcategory]` → status + product type (113 keys, all observed combinations). Stores `taxonomy_version`. |
| `taxonomy/validate_taxonomy.py` | Checks types are unique and exist, statuses are consistent, and (given `cleaned_data/`) every observed tuple has a mapping |
| `taxonomy/worksheet/…-filled.csv` | Snapshot of the review worksheet the JSON was generated from. **The JSON is the source of truth; the CSV is not regenerated.** |
| `normalizer.py` | `Normalizer` class. Builds a casefolded `(shop, category, subcategory)` index from the nested `aliases.json`, validates it at load time, and raises `MappingError` on unknown tuples. |
| `run_normalization.py` | Reads `cleaned_data/*.json`, writes `normalized_data/*.json` and `reports/normalization_report.json`. Writes to `normalized_data.tmp/` and swaps it in only when there are zero errors, so a failed run never leaves partial output. |
| `review_normalized.py` | Read-only review script. Prints counts per retailer and sample names per product type, comparison coverage, flagged-row checks and the `parent_only` / `unmapped` buckets. Writes `reports/normalization_review.txt`. |
| `tests/test_normalizer.py` | 7 tests: mapped, `parent_only` and `unmapped` lookups, null subcategory, casefolding, unknown-tuple failure, no input mutation, idempotency, version mismatch, and every observed tuple in `cleaned_data/`. |

**Run:**

```
python data_processing/taxonomy/validate_taxonomy.py cleaned_data
python data_processing/run_normalization.py
python -m pytest tests/test_normalizer.py
python data_processing/review_normalized.py
```

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

### Verified results (first real run)

| Check | Result |
|-------|--------|
| Validator on `cleaned_data/` | 0 errors, 0 warnings |
| Records in / normalized / errors | 2,975 / 2,975 / 0 |
| `mapped` | 2,389 (80%) |
| `parent_only` | 346 |
| `unmapped` | 240 |
| Unused alias keys | none |
| `tests/test_normalizer.py` | 7 passed |

Counts match the worksheet exactly.

### Worksheet results

| Status | Rows | Records |
|--------|-----:|--------:|
| mapped | 102 | 2,389 (80%) |
| parent_only | 7 | 346 |
| unmapped | 4 | 240 |
| **Total** | **113** | **2,975** |

`parent_only`: myG Accessories, Personal Care, Home Automation; Oxygen Kitchen Appliances; Pittappillil Chimney & Hob, Home Inverters & Batteries, Mobile Accessories.
`unmapped`: myG Home & Kitchen, myG Small Appliances, Oxygen Gadgets, Nandilath "Mobiles & Laptops → Accessories" (misfiled; the sample is a refrigerator).

### Guardrails for `normalizer.py`

1. **Unmapped-tuple detection:** ✅ a new retailer/category combination never silently falls through. An unknown tuple raises `MappingError`, the run fails, and the previous output is not replaced.
2. **Determinism / idempotency:** ✅ the normalizer reads `raw_*` fields when present; the same cleaned input always gives the same output, and re-running on normalized output changes nothing.
3. **Coverage in both directions:** ✅ every observed tuple has a key (validator), and every key is used (`unused_alias_keys` in the report).
4. **Version both files:** ✅ `Normalizer` refuses to load if `taxonomy.json` `version` differs from `aliases.json` `taxonomy_version`. Bump both together when a mapping changes.

### Downstream note

`unmapped` records (240) pass through with `category: null` and `product_type: null`. `parent_only` records (346) have a category but a null `product_type`. The database and API **must handle both** (the `listing_categories` columns are nullable for this reason).

### Review results

Rows reviewed: Nandilath **Cooktop** (25), Pittappillil **Mixer Grinders** (78), Pittappillil **Chimney & Hob** (54), Pittappillil **Home Inverters & Batteries** (12).

**No mapping changes were needed, so the taxonomy version stays at 1.0.**

| Row | Finding |
|-----|---------|
| Nandilath **Cooktop** (25) | Gas burner units, with about 4 possibly hobs. Stays mapped to Gas Stove. |
| Pittappillil **Mixer Grinders** (78) | Clean. |
| Pittappillil **Chimney & Hob** (54) | About 32 chimneys and 22 hobs. Stays `parent_only`; names could split it later. |
| Pittappillil **Home Inverters & Batteries** (12) | 7 inverters and 5 batteries (check "battery" before "inverter" if a rule is ever added). Stays `parent_only`. |

**Type coverage:** 30 of 48 types have 2+ retailers (18 have one). By retailer count: 1 retailer = 18 types, 2 = 24, 3 = 2, 4 = 4. Chimney and Hob show as Nandilath-only because Pittappillil's records are `parent_only`. Tablet is myG-only (108 records, likely truncated). The other single-retailer types (Iron, Chest Freezer, Monitor and so on) are genuine assortment differences.

---

## 🏷️ **19c. PHASE 2C: BRAND EXTRACTION** ✅

Adds `brand`, `brand_status` and `brand_candidates` to each normalized record. Brand extraction is a separate step: it never changes category, product type or name, and it is not product matching.

**Pipeline:** `normalized_data/*.json` → `brand_extractor.py` → `branded_data/*.json` + `reports/brand_report.json`

### Added fields

| Field | Values |
|-------|--------|
| `brand` | Canonical brand name from `brands.json`, or `null` |
| `brand_status` | `matched`, `unknown` or `review` |
| `brand_candidates` | List of brands found in the name when status is `review`, else `null` |

| Status | Meaning | `brand` |
|--------|---------|---------|
| `matched` | Exactly one brand found | the brand |
| `unknown` | No brand in the list found | `null` |
| `review` | Two or more different brands found (conflict) | `null` (candidates listed) |

```json
{
  "name": "Samsung Galaxy S25 5G | 12 GB | 256 GB",
  "shop": "myG",
  "category": "Mobiles & Tablets",
  "product_type": "Mobile Phone",
  "mapping_status": "mapped",
  "taxonomy_version": "1.0",

  "brand": "Samsung",
  "brand_status": "matched",
  "brand_candidates": null
}
```

### Design decisions

- **Explicit list, no guessing.** `brands.json` maps each canonical brand name to its aliases. A name with no matching alias gets `brand: null`, `brand_status: "unknown"`, and is listed in the report.
- **Whole-token matching** on the casefolded name with punctuation removed. An alias never matches inside another word.
- **A match fully inside a longer match is dropped** ("Prestige" inside "TTK Prestige"), so it is not counted as a conflict.
- **Conflicts go to `review`, not to a guess.** If two or more different brands remain after that, `brand` stays `null` and the brands are stored in `brand_candidates` (in the order they appear in the name). This replaces the earlier "earliest match wins" rule.
- **`start_only` brands** match only at the start of the name: `HP`, `Nothing`, `Vu`, `Noise`, `Urban`, `Google`, `Apple`, `Sharp`, `Lifelong`. Reasons: "1.5 HP" is an air conditioner rating; "Active Noise Cancellation"; "Google TV" and "Google Assistant" are software, not the manufacturer (this alone removed 93 false conflicts on TVs); "Plain Apple Water Jug"; "Sharp Adjustable".
- **The Xiaomi family is one brand.** `Redmi`, `Mi` and `Poco` are aliases of `Xiaomi`, so every product in the family carries the same `brand` value. **This reverses the earlier decision to keep sub-brands separate.** The product line stays in the name ("Redmi Note 14") for Phase 5 matching.
- **Solarium is not a brand.** It is a Crompton product line; names contain "Crompton" and match through that word.
- **Aliases fix retailer typos and short forms explicitly**, so the canonical spelling is what gets stored (e.g. `Fujifilm` ← "Fufifilm", `Elgi` ← "Elgiultra", `V-Guard` ← "V-GURAD", `Eureka Forbes` ← "Forbes"/"EForbes", `Morphy Richards` ← "Morphy", `realme` ← "realmetws", `Bosch` ← "B0SCH", `IFB` ← "IFBFF").
- **The brand file rejects duplicate aliases.** Two brands claiming the same alias fails loudly at load time. JSON itself silently keeps the last of two identical keys, so never add a brand that already exists; edit its existing entry instead.
- **Same-company conflicts are accepted into `review` for the MVP.** Eureka Forbes + Aquaguard (4) and Samsung + Symphony (2, from "Q-Symphony") are correct brands that land in `review`. `same_company` groups or `ignore_phrases` could fix them later if the volume grows.
- **Read-only on everything else.** All existing fields pass through unchanged, and the same input always gives the same output.

### Files

| File | Purpose |
|------|---------|
| `data_processing/brands.json` | Canonical brand → aliases, plus the `start_only` list (versioned, hand-made). Its `version` is stored on every listing as `brands_version`. Current version `1.1` (bumped after the `review` / Xiaomi / `start_only` changes); bump it with every edit. |
| `data_processing/brand_extractor.py` | `BrandExtractor` class: matching, `classify()` (brand, status, candidates), `enrich()`, brand-file validation |
| `data_processing/run_branding.py` | Runner: reads `normalized_data/`, writes `branded_data/` (via a `.tmp` swap) and `reports/brand_report.json` (includes review groups) |
| `tests/test_brands.py` | 12 tests: case and punctuation, brand not first word, aliases and longest match, `start_only`, unknown is `None`, purity/idempotency, duplicate alias rejected, conflict goes to `review`, Google mid-name ignored, nested alias is not a conflict, Xiaomi family is one brand, `brand_candidates` null unless `review` |

### Run

```
python -m pytest tests/test_brands.py
python data_processing/run_branding.py
```

### Results (accepted run)

| Metric | Value |
|--------|------:|
| Records | 2,975 |
| Matched | 2,942 |
| Review | 10 |
| Unknown | 23 |
| **Match rate** | **98.9%** |

| Retailer | Matched | Review | Unknown |
|----------|--------:|-------:|--------:|
| Nandilath G Mart | 742 | 2 | 5 |
| Oxygen | 237 | 0 | 8 |
| Pittappillil | 865 | 7 | 6 |
| myG | 1,098 | 1 | 4 |

**Review groups (10 records):** Faber + LG (4; "LG" is a model code in "...FL LG 90 Chimney", so Faber is probably correct), Eureka Forbes + Aquaguard (4), Samsung + Symphony (2).

Progress across iterations: 87.5% → 95.5% → 98.1% → 99.0% → 99.2% → 98.9%. The last dip is intended: 10 records moved from a guessed or uncertain brand to `review`. Before the `start_only` and Xiaomi changes there were 113 two-brand conflicts, 93 of them involving Google.

### Review

- **Wrong-match check done.** The top brands are LG, Samsung, V-Guard, Bosch and IFB, all plausible. Generic-word brands barely fire: Kent 2, Orient 6, Elgi 7, Dace 9, Mobilla 3, Noise 2, Asian 1, Cello 1, Meyer 1, Urban 1. Both Kent hits were real Kent products.
- **Unused brands:** 20 entries matched nothing (mostly phone and accessory brands the retailers do not stock in this data, e.g. iQOO, Infinix, Itel, Lava, Honor, Boult, Fire-Boltt). Harmless; prune later if wanted.
- **Remaining unknowns (23):** mostly one-off brands and product words. The `MR LED Smart TV` group (7) has not been inspected.

> **MVP decision:** 98.9% matched is accepted. `unknown` and `review` records keep `brand: null` and are listed in `reports/brand_report.json`. New brands are added by editing `brands.json` and rerunning.

> **Optional cleanup batch (not required):** Hykon, Vidiem, Everest, Kuhl, Fingers, Indus Valley, Aquaneeta as new brands, and aliases `Blueberry` ← "blueberrys". A few small brands added earlier (Lockify, GDOT, Ogera, Toxen, Heugor, Hapi, Onix) could not be confirmed online; they are kept because the retailer listing is the source of the name.

### Known limits

- Matching uses the product **name only**, so a brand word that is really part of a model name could mis-tag, or turn into a false `review`. The report's `brand_counts` and `review_groups` are the places to spot this.
- It only sees brands that are in the list: "Spigen Case for Samsung Galaxy" would still be tagged Samsung. A "for / compatible with" context rule is not built.
- Product words at the start of a name (`Mixer`, `Chimney`, `Inverter`, `Water`) show up as unknown leading tokens in the report even though the real brand is usually matched later in the name. Ignore those.

---

## 🗄️ **19d. PHASE 3: POSTGRESQL** ✅

Loads `branded_data/` into PostgreSQL. The database stores listings, their canonical and raw categories, and a price history that grows with every load.

```
branded_data/*.json  ->  db/loader.py  ->  PostgreSQL (quote_yard)
```

### Schema

```
retailers (1) ──< listings (1) ──< listing_categories
                     │
                     ├──< price_history
                     │
                     └──> canonical_products (nullable, empty until Phase 5)
```

**`retailers`**: `id`, `name` (unique), `base_url`. Seeded with exactly `myG`, `Oxygen`, `Pittappillil`, `Nandilath G Mart`. The loader fails on an unknown shop instead of creating one. `base_url` is the retailer's origin (scheme + host, no trailing slash), seeded by `create_tables.py` and only filled when empty:

| Retailer | `base_url` |
|----------|------------|
| myG | `https://www.myg.in` |
| Oxygen | `https://www.oxygendigitalshop.com` |
| Pittappillil | `https://www.pittappillilonline.com` |
| Nandilath G Mart | `https://nandilathgmart.com` |

Every one of the 2,965 loaded listing URLs starts with its retailer's origin (one origin per retailer).

**`listings`**: one row per `(retailer_id, url)`.

| Column | Notes |
|--------|-------|
| `id`, `retailer_id`, `url`, `name` | `(retailer_id, url)` is unique; `name` is the original name, untouched |
| `brand`, `brand_status`, `brand_candidates` | `brand_status` in `matched` / `unknown` / `review`; `brand_candidates` is JSONB, set only for `review` |
| `current_price` | integer rupees, `NOT NULL`, `> 0` |
| `availability` | `In stock` / `Out of stock` / `Unknown` (CHECK constraint) |
| `first_seen_at`, `last_seen_at` | timestamptz |
| `canonical_product_id` | nullable FK, stays null until Phase 5 |
| `taxonomy_version`, `brands_version` | recorded so rows can be reprocessed later |

Constraint rules in the database itself: `brand_status = 'matched'` exactly when `brand` is set; `brand_status = 'review'` exactly when `brand_candidates` is set.

**`listing_categories`**: one row per distinct `(listing, raw_category, raw_subcategory)`.

| Column | Notes |
|--------|-------|
| `category`, `product_type` | canonical values, both nullable (`unmapped` / `parent_only`) |
| `mapping_status` | `mapped` / `parent_only` / `unmapped` |
| `raw_category` | `NOT NULL` |
| `raw_subcategory` | nullable; empty strings become NULL |

Uniqueness uses a unique index on `(listing_id, raw_category, COALESCE(raw_subcategory, ''))`, so two NULL subcategories count as the same row on every PostgreSQL version.

**`price_history`**: `id`, `listing_id`, `price` (`> 0`), `availability`, `recorded_at`; index on `(listing_id, recorded_at DESC)`.

**`canonical_products`**: created empty in Phase 3; extended in Phase 5 (migration `0001`) with the match columns, see Section 23.

`category` and `product_type` are plain text, not foreign keys to lookup tables. The JSON taxonomy stays the single source of truth, and `taxonomy_version` covers drift. Tables are created with `create_all` on a new database (then stamped at the Alembic head); since Phase 5, schema changes are **Alembic migrations** in `db/migrations/` (`alembic upgrade head`).

### Why the category join key is the raw pair

Home Theater and Sound Bars both map to Soundbar. Keying on the canonical `(category, product_type)` would merge them and lose which retailer category each came from. Keying on the raw pair keeps the provenance, and `SELECT DISTINCT product_type` still gives the distinct canonical types. For the same reason the raw values live on the join row, not on the listing (a URL in two subcategories has two raw pairs).

### Loader rules (`db/loader.py`)

1. **All or nothing.** Every record is validated first (shop, URL, name, positive integer price, availability, statuses, brand/candidates consistency). Any invalid record fails the whole load and nothing is written. The load runs in one transaction.
2. **Order and dedupe.** Files are read in sorted filename order and records in file order. Records are deduped by `(shop, url)`; the **first record in load order wins**, and a warning is logged if a later duplicate differs in name or price. An existing database row never decides which record wins.
3. **Categories.** Every distinct raw pair seen for a URL becomes one `listing_categories` row; changed canonical values on an existing pair are updated.
4. **Price history.** A row is added on first sighting, on any price change, and when a **known** availability differs from the **last known** availability. `Unknown` is never treated as a change, and the first known value after a run of `Unknown` is still recorded.
5. **Never delete listings.** A listing missing from a scrape is not marked gone, because myG's truncated categories would falsely look removed. `last_seen_at` shows freshness.
6. **Idempotent.** Re-running the same data inserts nothing and adds no history rows; it only refreshes `last_seen_at`.
7. **Dry run.** `python -m db.loader --dry-run` does everything and rolls back.

### Files

| File | Purpose |
|------|---------|
| `db/session.py` | Engine and connection URL (`QUOTE_YARD_DATABASE_URL`, default `postgresql+psycopg:///quote_yard`) |
| `db/models.py` | SQLAlchemy models, check constraints, indexes |
| `db/create_tables.py` | Creates the tables and seeds the four retailers with their `base_url`; fills an empty `base_url` but never overwrites one (safe to repeat) |
| `db/loader.py` | The loader described above |
| `tests/test_db_models.py` | 6 tests: valid listing, duplicate `(retailer, url)`, bad availability, zero price, review requires candidates, duplicate NULL-subcategory category. Each test rolls back; they skip if PostgreSQL is unreachable. |
| `tests/test_loader.py` | 16 tests: first load, rerun adds nothing, price change, `Unknown` availability, duplicate URL (first wins, categories merged), same pair twice, re-mapping, review candidates, unknown shop, 7 invalid-record cases |

### Run

```
python -m db.create_tables
python -m pytest tests/test_db_models.py tests/test_loader.py -v
python -m db.loader --dry-run
python -m db.loader
```

### Results

| Check | Result |
|-------|--------|
| Records read | 2,975 |
| Unique `(shop, url)` | 2,965 (matches 2,975 minus the 10 duplicate URL groups) |
| `listings` | 2,965 |
| `listing_categories` | 2,975 (every duplicate sat under a different raw category) |
| `price_history` | 2,965 (one first-sighting row each) |
| Duplicate-URL warnings | 0 (the duplicates agree on name and price) |
| Listings per retailer | myG 1,103 · Nandilath G Mart 739 · Oxygen 245 · Pittappillil 878 (all 10 duplicate URLs were Nandilath: 749 records became 739 listings) |
| Reruns (dry run, load, load again) | 0 inserted, 0 history rows, 0 category changes |
| Tests | 6 (models) + 16 (loader) passed |
| `brands_version` | `1.1` on all 2,965 listings (bumped after the first load; the loader updated the stored version without adding any rows) |

Whole project: 41 tests (7 normalizer, 12 brands, 6 models, 16 loader).

### Known limits

- Availability is only `In stock` or `Unknown` in current data (2,796 / 179). The out-of-stock path is allowed by the schema but unexercised (see open item 3).
- `price_history` only grows when the loader runs. Price history is therefore only as good as the scrape schedule (Phase 7).
- Full-text / fuzzy search is not set up; plain `ILIKE` is the plan for Phase 4. Add a `pg_trgm` index if it gets slow.

---

## 🔌 **19e. PHASE 4: FASTAPI** ✅

A **read-only** HTTP API over the loaded data, under `/api/v1`. Interactive docs at `/api/v1/docs`.

```
React -> FastAPI -> SQLAlchemy -> PostgreSQL
```

### Endpoints

Canonical products do not exist until Phase 5, so the API is **listings-based**. There is no `/products` or `/compare/{product_id}` yet.

| Method | Endpoint (under `/api/v1`) | Purpose |
|--------|----------------------------|---------|
| GET | `/health` | API and database check |
| GET | `/retailers` | Name, `base_url`, listing count |
| GET | `/listings` | Search and filter, paginated, with `total` |
| GET | `/listings/summary` | Per-retailer count, min / max price and cheapest listing for the same filters (an interim, rough comparison; it does not claim the listings are the same product) |
| GET | `/listings/{id}` | One listing with its retailer and all category rows |
| GET | `/listings/{id}/prices` | Price history, oldest first |
| GET | `/product-types` | Types with listing counts, total and per retailer |
| GET | `/brands` | Brands with listing counts |

**`/listings` filters:** `q`, `retailer`, `category`, `product_type`, `brand`, `min_price`, `max_price`, `availability`, `seen_since`. **Sort:** `price_asc`, `price_desc`, `name`. **Paging:** `limit` (default 20, max 100) and `offset`.

### Design decisions

- **`/listings/summary` replaced the earlier "type comparison" idea.** The cheapest Mobile Phone at each shop is only each shop's cheapest phone (a feature phone at 1,099 rupees on myG), so a type-level minimum is not a comparison. The summary applies the same filters as the search, so adding `q` or `brand` compares like with like. It lists **every** retailer, with zeros where nothing matches.
- **`/api/v1` prefix** on every route, so Phase 5 can change response shapes without breaking the React app.
- **Synchronous routes and SQLAlchemy.** FastAPI runs plain `def` routes in a thread pool; no async driver is needed at this scale.
- **Search:** every word in `q` must appear in the name (`ILIKE`, ANDed), with `%` and `_` in user input escaped literally. About 3,000 rows need no index.
- **`EXISTS`, not `JOIN`, for category filters.** 10 listings sit under two category rows, so a join would return duplicates. Category and type must match on the same category row.
- **Stable ordering:** every sort adds `id` as a tie-breaker, so pages do not shuffle.
- **Prices** are integer rupees. `brand`, `category` and `product_type` can be null in responses. `brand_status` is always included so the frontend can treat `review` / `unknown` differently.
- **Freshness:** `last_seen_at` is returned and `seen_since` filters on it, because the loader never deletes listings.
- **Route order matters:** `/listings/summary` is declared before `/listings/{listing_id}`, or "summary" would be read as an id (a test guards it). Ids outside the 32-bit range return 422.

### Basic protection (built)

| Protection | How |
|------------|-----|
| Read-only database access | The API engine sets `default_transaction_read_only=on`, so any write fails (tested). For deployment, also use a separate SELECT-only database role. |
| Query timeout | `statement_timeout` of 5 seconds on the API engine (tested) |
| Pagination caps and validation | `limit` max 100; `q` max 100 characters and 8 words; inverted price ranges and unknown values return 422 |
| CORS | `GET` only, from the origins in `QUOTE_YARD_CORS_ORIGINS` (default `http://localhost:5173`) |
| Rate limiting | Own in-process sliding-window limiter (`api/ratelimit.py`, no dependencies): per client address, default 120 requests per minute, set with `QUOTE_YARD_RATE_LIMIT` (`0` turns it off). `/health` is exempt. Over the limit: `429` with `Retry-After`, and CORS headers are still present so the React app can read it. At most 10,000 clients are tracked. It is **per process** and resets on restart, which is fine for one worker. Behind a reverse proxy, start uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy address>` so visitors are counted separately. |
| Input safety | All values are parameterized; no raw SQL from user input |

### Files

| File | Purpose |
|------|---------|
| `api/main.py` | App factory, `/api/v1` prefix, CORS, rate-limit middleware |
| `api/deps.py` | Read-only engine with statement timeout, session dependency |
| `api/schemas.py` | Pydantic response models (ORM objects are never returned directly) |
| `api/filters.py` | Shared listing filters, used by `/listings` and `/listings/summary` |
| `api/ratelimit.py` | The limiter and its ASGI middleware |
| `api/routes/` | `health.py`, `catalog.py`, `listings.py` |
| `tests/conftest.py` | Turns the limiter off for the shared test app; the rate-limit tests build their own apps |

### Results

| Check | Result |
|-------|--------|
| API tests | 62 (health 6, catalog 6, listings 19, summary/detail/prices 17, rate limiting 14) |
| Whole project | **103 tests pass** |
| Live `/listings` total | 2,965 |
| Live filter checks | Oxygen refrigerators 34 · myG televisions 108 · Oxygen phones 58 (all match the retailer record counts) |
| Live `/listings/summary?product_type=Mobile Phone` | 277 = myG 108 + Oxygen 58 + Pittappillil 28 + Nandilath 83 |

### Known limits

- **No relevance ranking:** a search for "samsung" sorted by price can list cheap accessories first.
- **The same phone appears under different names** (Oxygen "REDMI A7 (Sky Blue, 64 GB)" and Nandilath "Redmi A7 (3GB RAM/64GB Storage, Sky Blue)", both at 12,999 rupees). That is the Phase 5 matching problem; the summary shows both, unmatched.
- **Price history is one point per listing** until the scheduler (Phase 7) runs.
- The rate limiter is per process; use a shared store only if the API ever runs as several workers.

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

**Normalization (Phase 2B):** built, tested, reviewed, verified

- Category and subcategory audit complete (27 category names, 85 subcategory values)
- Mapping worksheet: 113 unique `(retailer, category, subcategory)` combinations, all classified
- `taxonomy.json` v1.0 (14 categories, 48 product types) and `aliases.json` generated; `validate_taxonomy.py` passes on real data (0 errors, 0 warnings)
- `normalizer.py` and `run_normalization.py` built; 2,975 / 2,975 records normalized, 0 errors (2,389 mapped, 346 `parent_only`, 240 `unmapped`)
- 7 tests passing; all four guardrails implemented
- `review_normalized.py` built; review of the four flagged rows complete, **no mapping changes needed, version stays 1.0**
- **MVP decision:** 80% of records fully mapped; `parent_only` and `unmapped` pass through unchanged; rule-based layer deferred

**Brand extraction (Phase 2C):** built, tested, accepted

- `brands.json`, `brand_extractor.py`, `run_branding.py`, `tests/test_brands.py` (12 tests passing)
- 2,942 matched, 10 `review`, 23 unknown (98.9% matched); wrong-match check done
- `review` status added for multi-brand conflicts (`brand: null` plus `brand_candidates`)
- Xiaomi family merged (Redmi, Mi, Poco); `Google`, `Apple`, `Sharp`, `Lifelong` made `start_only`
- **MVP decision:** accept 98.9%; unknown and review records reported, not guessed

**PostgreSQL (Phase 3):** built, tested, loaded

- Schema with database-level constraints (price, availability, brand status, review/candidates pairing, NULL-safe category uniqueness)
- `db/loader.py`: validated, transactional, first-record-wins dedupe, idempotent, with a dry-run mode
- 2,965 listings, 2,975 listing_categories, 2,965 price_history rows loaded; reruns add nothing
- 22 DB tests passing (6 models, 16 loader)
- Retailer `base_url` seeded; all 2,965 listing URLs match their retailer's origin
- `requirements.txt` and `requirements-dev.txt` created; Playwright's Chromium is installed separately (`playwright install chromium`)

**FastAPI (Phase 4):** built, tested, verified against live data

- Eight read-only endpoints under `/api/v1` (health, retailers, listings with filters / sorting / paging, per-retailer summary, listing detail, price history, product types, brands)
- Read-only database connection, 5-second statement timeout, pagination caps, GET-only CORS, in-process rate limiting
- 62 API tests; **103 tests pass across the project**; live counts match the retailer record counts
- `httpx2` replaces `httpx` for the test client (Starlette 1.x prefers it)

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

**Phase 5 (product matching):** next. The first step is a read-only extraction report over the 277 mobile-phone listings (brand, model, RAM, storage, colour), before any matching code or schema change. Phase 4A (accounts) follows after Phase 5.

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
| 3 | **Out-of-stock path:** unverified end to end. Current data has only `In stock` and `Unknown`; Oxygen's tested category had nothing out of stock. |
| 4 | **Pittappillil subcategories:** 55 URLs are configured but only 48 subcategories appear in the data. Find which 7 returned nothing and confirm that is expected, not a silent scraper stop. |
| 5 | ~~**Run the validator on real data**~~ ✅ Done: 0 errors, 0 warnings. |
| 6 | **myG truncation:** 8 of 11 myG categories have exactly 108 records (9 pages x 12), matching the 403 at page 10 (seen again in the normalized output and in live API counts). The cause is not yet known, and the fix depends on it. Planned tests, one at a time: **A** open `/mobile-phones/page-9/`, `page-10/` and `page-11/` in a normal browser (if page 10 loads, the block targets the automated browser; if it is blocked there too, the site caps pagination depth); **B** run `python scrapers/myg_scraper.py --only mobiles --max-pages 12` to see where it stops; **C** check whether sorting (price ascending / descending) or filters change the URL, since each view can expose up to 108 products. Check `robots.txt` and the site's terms first, and do not spoof headers or rotate identities to evade a block. If the cap is deliberate, ask myG for a product or price feed. Until it is fixed, make no "cheapest" claim in categories where myG coverage could change the answer. Runs in parallel; does not block Phase 5. |
| 7 | ~~**Unknown brands**~~ ✅ Accepted at 98.9% matched (23 unknown, 10 review). An optional cleanup batch is listed in Section 19c. |
| 8 | **Unmapped coverage (20%):** 346 `parent_only` and 240 `unmapped` records. Accepted for the MVP. Revisit with a name-rule layer or an `Earbuds` type if it limits comparison coverage. |
| 9 | **Brand `review` records (10):** resolved by hand or by a later rule. Only Faber + LG (4) is true ambiguity; Eureka Forbes + Aquaguard (4) and Samsung + Symphony (2) are correct brands flagged by design. |
| 10 | ~~**Availability values**~~ ✅ Checked: only `In stock` (2,796) and `Unknown` (179). Constraint locked to `In stock` / `Out of stock` / `Unknown`. |
| 11 | **Scraper layout:** a repo sketch showed `scrapers/` as folders while this plan describes single files. Confirm and update Sections 7, 12 and 13 if reorganized. |
| 12 | **End-to-end pipeline command:** there is no single command yet that runs scrape → clean → normalize → brand → load. Needed for Phase 7. |
| 13 | **Loader URL-origin warning (proposed, undecided):** warn, not fail, when a record's URL does not start with its retailer's `base_url`. Catches a scraper pointing at the wrong site; a warning rather than an error in case a retailer uses a second domain. Small change plus one test. |
| 14 | **Phase 4A open questions:** is the React frontend part of the sprint? Confirm the token form (opaque token in an httpOnly cookie, not JWT); whether a CAPTCHA provider is acceptable for open sign-up; which email provider and sending domain to use for OTP (needs SPF and DKIM records for deliverability). See Section 23. |
| 15 | ~~**`brands_version`**~~ ✅ Bumped to `1.1`; all 2,965 listings carry it (the loader updated the version without adding rows). Bump it with every edit to `brands.json`. |
| 16 | **Public deals:** with matching now before accounts, the teaser is generated from Phase 5 matches and price history; hand-curated deals remain only as a manual override. Until Phase 5 exists there is no honest way to compute a deal (one price point per listing, no stored list prices). |
| 17 | **Platform gating changes the public API:** requiring login for search and listings means the Phase 4 routes (currently open) gain an authentication dependency, and their tests use an authenticated client. Free open sign-up is a speed bump for scrapers, not a barrier. |
| 18 | ~~**Phase 5 open questions**~~ ✅ Phones first; colour not in the key; `review` / `unknown` brands excluded; feature phones match on TA code. See Section 23. |

## ➡️ **Next major work**

The four scrapers are the data-collection layer. **Do not add Croma yet.**

```
Four retailer raw data -> Cleaning -> Normalization -> Brand Extraction -> PostgreSQL -> FastAPI
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

## ➡️ **Phase 5: product matching (starting with mobile phones)**

Phases 1 to 4 are complete (Sections 19a to 19e): 2,965 listings are loaded and served by the read-only API, and 103 tests pass.

**Order decision:** Phase 5 (matching) runs **before** Phase 4A (accounts). Matching is the core of a price comparison site, and it lets the public deal teaser be computed from real matches instead of hand-picked ones. Accounts then protect a platform that already compares prices.

**Housekeeping:** ✅ `brands.json` is version `1.1` and all 2,965 listings carry it (verified). If not already done, commit the Phase 4 work (`api/`, the new tests, `requirements*.txt`, `brands.json`, this plan) and push.

### Why mobile phones first

- 277 listings are typed `Mobile Phone`: myG 108, Oxygen 58, Pittappillil 28, Nandilath 83. It is the largest overlap across the four retailers.
- Names carry brand, model, RAM and storage, but in four different formats:

| Retailer | Example name |
|----------|--------------|
| Oxygen | `REDMI A7 (Sky Blue, 64 GB) (3 GB RAM)` |
| Nandilath G Mart | `Redmi A7 (3GB RAM/64GB Storage, Sky Blue)` |
| myG | `realme 16 Pro+ 5G \| 12 GB \| 256 GB \| Master Gold` |
| Pittappillil | `MOTOROLA SMART G06 POWER 4G (4+64GB) PANTONE LAUREL OAK` |

- The two Redmi A7 listings are the same phone at the same price (12,999 rupees); today the API shows them as unrelated.
- Appliances, TVs and laptops usually carry a model code, so they can follow once phones work.

**Limit of the starting set:** myG is truncated at 108 records (open item 6), so a match shows only what is in the data. No "cheapest" claim without coverage.

### Approach (proposed; to settle after the extraction report)

| Step | Detail |
|------|--------|
| 1. Extraction report (read-only) | A script parses brand, model, RAM, storage and colour from the 277 names and reports how many parse cleanly, which formats occur, and which names are ambiguous. **No database writes and no matching yet.** |
| 2. Match key | `(brand, model, RAM, storage)`: all four must agree. Colour is not part of the key at first (retailers spell colours differently, and one phone in two colours is still one product). Anything ambiguous goes to a **review report**, never forced, the same approach as brand conflicts. |
| 3. Rules | Explicit patterns only, deterministic and idempotent, versioned (`matching_version`). Category-specific parsing is added now because matching is the real requirement that Section 15 asks for. Listings with `review` or `unknown` brand are excluded from matching. |
| 4. Verification | A hand-check of a sample of matched groups (for example 20) with **zero wrong matches** before anything is written to the database |
| 5. Schema | `canonical_products` is empty today, so it can be recreated with the extra columns (model, RAM, storage, match key); `listings.canonical_product_id` already exists. Consider Alembic once the schema starts changing. |
| 6. Writing matches | A separate runner sets `canonical_product_id`; the API itself stays read-only |
| 7. API | `/products`, `/products/{id}`, `/products/{id}/prices` and `/compare/{product_id}` replace the interim per-retailer summary for matched products |

Matching stays **separate** from scraping, normalization and brand extraction (Section 3.3).

### Progress (steps 1 to 5 done; no matches written to the database yet)

| Step | Status |
|------|--------|
| 1. Extraction report | ✅ `matching/extract_phones.py` → `reports/phone_extraction_report.txt`. RAM and storage parsed for 246 / 277; gaps found: Nandilath drops "Galaxy", `V70FE` vs `V70 FE`, `Nothing Phone (4a)` gave an empty model, network missing on one side, Apple has no RAM, feature phones have no specs, bundles ("Photographer Kit", "Without Adapter"). |
| 2-3. Matcher (`matching_version` 1.1) | ✅ `matching/phone_matcher.py` → `reports/phone_match_report.txt` + `reports/phone_matches.json`. Key `(brand, model, network, RAM, storage, package)`; colour and box contents never in the key. |
| 4. Verification | ✅ All 32 cross-retailer groups checked by hand: **0 wrong matches**. Two runs give identical output. |
| 5. Schema | ✅ Alembic introduced (`alembic==1.20.0`, `alembic.ini`, `db/migrations/`). Migration `0001`: `canonical_products` gains `model`, `network`, `ram_gb`, `storage_gb`, `package`, `ta_code`, `match_key` (unique), `matching_version`; `brand` becomes `NOT NULL`; checks: network in 2G-5G, RAM/storage > 0, storage or TA code required. `listings` gains `box_note`. Rehearsed on a copy (upgrade, downgrade, upgrade, `alembic check` clean) and on a new database; live database backed up, then upgraded (2,965 listings unchanged). `CanonicalProduct.listings` / `Listing.canonical_product` relationships added. 8 new model tests. |

**Rules:** only `brand_status: matched` takes part · model key is the name head, casefolded, brand and filler words dropped, spaces removed · `galaxy` is optional for Samsung · `Phone (4a)` → `4a` · network read from the whole name, `LTE` = 4G; a listing with no network joins its model's network when only one is seen, otherwise review · **bundles** (`photographer kit`) are part of the key, so a bundle never merges with the plain phone · **box contents** (`without adapter`) are not: the phone merges, each listing keeps a `box_note`, and the group lists its `box_notes` (decided in 1.1) · **retailer words**, only when verified against the retailer's own spec table and only straight after the brand: Pittappillil `SMART` (its Model field reads `4B 5G` for "NOTHING SMART 4B 5G" and `G06 POWER 4G` for "MOTOROLA SMART G06 POWER 4G", checked 2026-10-29). `smart` is **not** a global filler word (Smart TV, Smart Watch, V-Guard Smart inverters) · Apple ignores RAM · phones with no RAM and storage match on brand + `TA-xxxx` code (decided) · groups with a price spread over 25% are kept but flagged.

**Results (1.1):** 113 canonical products from 276 listings; **32 sold by 2+ retailers** (28 by two, 4 by three), covering 121 listings. 1 skipped (Nokia 130, no specs and no TA code). 0 review items. 1.0 had 116 / 30 and 3 review items; 1.1 resolved them: Nothing Phone (4b) 8/256 now matches Pittappillil "Smart 4B" (both 40,999), and Samsung A17 6/128 and 8/128 merge with Oxygen's "Without Adapter" listings (box note kept).

**Tests:** `tests/test_phone_matcher.py`, 18 tests (four formats one group, variant words kept apart, RAM/storage must agree, colour ignored, Galaxy/spacing, Nothing brackets, LTE vs 5G, missing network joins / goes to review, bundle key, box note merges and is tracked, Pittappillil `SMART` only after the brand, Apple RAM, partial specs, TA codes, TA conflict, untrusted brand, price spread, order independence). Whole project: **129 tests pass** (after step 5).

**Schema commands:** new database `python -m db.create_tables` (creates and stamps); existing database `alembic upgrade head`; drift check `alembic check`.

**Next:** step 6 (a runner that writes the groups and sets `listings.canonical_product_id`), step 7 (`/products` and `/compare` endpoints).

### Open questions

| # | Question | Proposal |
|:-:|----------|----------|
| 1 | Start with mobile phones only? | Yes |
| 2 | Is colour part of the match key? | No, kept as a listing attribute |
| 3 | `review` / `unknown` brand listings? | Excluded from matching |

### Parallel track: the myG 108-record cap

The scraper stops at page 10 because myG returns 403. The cause decides the fix, so test one thing at a time (open item 6): open pages 9, 10 and 11 in a normal browser; run the scraper with `--max-pages 12`; check whether sorting or filters expose more products. Check `robots.txt` and the terms first. Do not spoof headers or rotate identities to evade a block; if the cap is deliberate, ask myG for a product or price feed. After any re-scrape, the pipeline order is `myg_scraper.py` then `run_cleaning.py`, `run_normalization.py`, `run_branding.py` and `python -m db.loader`; the loader only adds or updates, so nothing needs deleting first.

---

## ➡️ **Phase 4A: accounts, watchlist and the public deal teaser** (after Phase 5)

Phase 4A adds accounts and the first user-facing features on top of the API. **Vendor accounts are out of scope** (see "Future" below). The five-day plan below now needs about one more day for email verification; how the sprint is scheduled relative to Phase 5 is still to be planned.

**Before starting:** install a password-hashing package (`pip install argon2-cffi`; if it has no Python 3.14 wheel, use the standard-library `hashlib.scrypt`).

### Product flow (decided)

1. **Public landing page:** one or two featured deals, **no search bar**. A visitor who clicks a deal is sent to login / registration before seeing full product details.
2. **After login, the dashboard:** search bar, product listings, filters, per-retailer price comparison, account details and personal watchlist.
3. **Watchlist:** registered users save products, view them later and remove them.
4. **Truthful deals:** public previews use verified prices and genuine product matches. Nothing is advertised as "cheapest" unless the data supports the claim.

### Decisions

| # | Decision | Status |
|:-:|----------|--------|
| 1 | First user features: public deal teaser + personal watchlist | Decided |
| 2 | Registration: **open sign-up** with email and password | Decided |
| 3 | The full platform (search, listings, summary, catalog, watchlist) **requires login**; public access is limited to the landing page's deal teaser | Decided |
| 4 | Token-based authentication and secure password hashing | Decided (token form proposed below) |
| 5 | **Email verification by OTP** (changed from "later") | Decided (details proposed below) |
| 6 | Basic protection against automated registration and login abuse | Decided (measures proposed below) |
| 7 | Vendor accounts and local shop deals: a separate future phase | Decided |
| 8 | Phase 5 (matching) comes before Phase 4A | Decided |

### Email verification by OTP (proposed details)

| Rule | Proposal |
|------|----------|
| Code | 6 digits from Python's `secrets`, stored hashed, never in plain text |
| Lifetime | 10 minutes, single use; a new code cancels the old one |
| Guessing | 5 wrong attempts invalidate the code |
| Sending limits | 60-second resend cooldown; sends capped per email address and per IP per hour (this also stops the site being used to spam someone's inbox) |
| Unverified accounts | Cannot use the platform until the code is entered |
| Reuse | The same mechanism later handles "forgot password" (until then an admin command resets passwords) |
| Development and tests | A "console" backend prints the code in the terminal; tests use a fake sender |
| Production | SMTP settings from environment variables. Real delivery needs a provider and your own domain with SPF and DKIM records, or the codes land in spam. Choose before real users sign up. |

### Proposed refinements (to confirm)

| Topic | Proposal |
|-------|----------|
| Token form | An **opaque random token**, not JWT. Only its SHA-256 hash is stored in the database, so a database leak does not expose live sessions. It is delivered in an **httpOnly, SameSite=Lax cookie** (`Secure` in production), so page scripts cannot read it; this is safer than keeping a token in `localStorage`. The same token table can later serve `Authorization: Bearer` clients. 14-day expiry; logout revokes it. |
| CSRF | A required custom header on every state-changing request, and CORS with credentials from the configured origins only |
| Password hashing | argon2id (`argon2-cffi`), or `scrypt` from the standard library. Length 10 to 128 characters, no composition rules, must differ from the email address |
| Login protection | Generic error ("invalid email or password"), equal response time for unknown emails, a short per-account backoff after repeated failures (in memory, resets on restart), and a stricter rate limit on `/auth/login` |
| Registration protection | A stricter per-IP rate limit on `/auth/register`, a daily cap on new accounts per IP, a hidden honeypot field, and optionally a CAPTCHA (a free provider such as Cloudflare Turnstile). Email verification adds a further barrier. |
| After login | A per-user rate limit in addition to the per-IP one, so a bot cannot farm accounts to scrape the gated data |

### What changes in the existing API

- A `require_user` dependency is added to the catalog and listings routers (and, after Phase 5, the products routes). `/health` and `/public/deals` stay open.
- Catalog and listing routes keep the **read-only** database connection. The rule becomes: **only the auth, watchlist and deal-admin code writes, through a separate connection, and only to the new tables.** For deployment, use two database roles (read-only, and write on the new tables only).
- The 62 existing API tests switch to an authenticated test client (a dependency override), and new tests prove that anonymous requests to every gated route return 401.

### The public deal teaser

With Phase 5 done first, deals are **generated from real matches**, not hand-picked:

| Rule | Detail |
|------|--------|
| Source | One canonical product matched across 2 or more retailers; prices come live from the matched listings and are never typed in. A hand-picked deal remains possible only as a manual override, with `verified_by` and `verified_at` recorded |
| Claims are generated from the data | For example "12,999 at Oxygen, 13,499 at Nandilath: save 500". The saving is the difference **between the listed retailers**, not against a list price (the scrapers do not store list prices) |
| "Cheapest" wording | Only as "cheapest of the N retailers listed here", and only when every tracked retailer that stocks the product is included. Never "cheapest in Kerala" |
| Auto-hide | A deal disappears when any matched listing is out of stock, was last seen more than 3 days ago, or the saving falls below a minimum |
| Coverage caveat | While myG is truncated at 108 records, do not claim "cheapest" in categories where myG coverage could change the answer |
| Public payload | Product name, retailer names, prices, saving and `checked_at`. **No retailer URLs**; full details and links appear after login |
| Later | With daily scrapes (Phase 7), real price drops can also qualify as deals |

### Watchlist

- `PUT /me/watchlist/{listing_id}` adds (repeating it is harmless), `DELETE` removes, `GET /me/watchlist` lists with the current price and availability. After Phase 5 a watchlist item can also point at a canonical product.
- `price_when_saved` is stored with each item, so a later "dropped since you saved it" view needs no schema change.

### Schema (new tables only; `create_all` adds them, listing tables are untouched)

| Table | Main columns |
|-------|--------------|
| `users` | `id`, `email` (case-folded, unique), `password_hash`, `is_active`, `email_verified_at`, `created_at`, `last_login_at` |
| `email_codes` | `id`, `user_id`, `code_hash`, `purpose` (verify / reset later), `expires_at`, `attempts`, `used_at`, `created_at` |
| `sessions` | `id`, `user_id`, `token_hash` (unique), `created_at`, `expires_at`, `revoked_at`. The model is named `UserSession`, to avoid clashing with SQLAlchemy's `Session` |
| `watchlist_items` | `user_id`, `listing_id`, `price_when_saved`, `created_at`; unique `(user_id, listing_id)` |
| `featured_deals` | `id`, `canonical_product_id`, `is_active`, `is_manual`, `verified_by`, `verified_at`, `created_at` |

### Endpoints (under `/api/v1`)

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/public/deals` | Public: 1 to 2 verified deals, no search |
| POST | `/auth/register` | Public, rate limited, abuse protected; sends the OTP |
| POST | `/auth/verify-email` | Public, rate limited, attempt limited |
| POST | `/auth/resend-code` | Public, cooldown and caps |
| POST | `/auth/login` | Public, stricter rate limit; verified accounts only |
| POST | `/auth/logout` | Logged in |
| GET | `/auth/me` | Logged in (401 otherwise) |
| GET / PUT / DELETE | `/me/watchlist`, `/me/watchlist/{listing_id}` | Logged in |
| all catalog, listing and product routes | | Now require login |

Admin tools: `python -m db.users` (list, deactivate, set-password) and `python -m db.deals` (create manual, list, deactivate).

### Six-day plan (five days plus email verification)

| Day | Work |
|:---:|------|
| 1 | Models (`users`, `sessions`), password hashing, register / login / logout / me, token cookie and CSRF header, tests |
| 2 | Email OTP: code generation and hashing, mail backends (console, fake, SMTP), verify and resend endpoints, send limits, tests |
| 3 | Abuse protections (auth rate limits, per-IP registration cap, honeypot, login backoff), gate the catalog and listing routes, per-user rate limit, update the API tests, `db.users` tool |
| 4 | Watchlist endpoints; `featured_deals` generation and `/public/deals` with the truthfulness rules; tests |
| 5 | Frontend: landing page with the deal teaser, register / verify / login pages, dashboard shell connected to the API |
| 6 | Dashboard: search, filters, per-retailer comparison, watchlist, account; end-to-end checks; plan update |

Days 5 and 6 assume the React prototype can be wired up that quickly; if the frontend is not in this sprint, they become backend hardening and API documentation.

**Dashboard wording:** until matching covers a category, the per-retailer comparison comes from `/listings/summary` and is labeled "per retailer, not matched products", consistent with the truthfulness rule.

### Open questions

1. Is the React frontend part of the sprint, or only the backend?
2. Confirm the token form (opaque token in an httpOnly cookie, not JWT).
3. Is a third-party CAPTCHA acceptable for open sign-up?
4. Which email provider and sending domain for OTP?

---

## 🏪 **Future: Phase 9, vendor accounts and local shop deals** (not in the current sprint)

Vendors should eventually be able to: register their shops with business identification details; keep a vendor profile (shop information, contact details); submit weekly deals, promotional offers, prices and validity periods; and manage or update what they submitted. Approved offers appear **alongside** scraped retailer data in listings and price comparisons.

**Principles:**

| Principle | Detail |
|-----------|--------|
| Separate storage | Vendor offers live in their own tables (not in `listings`), so scraped data is never mixed with submitted data |
| Validated and matched | An offer is linked to the correct **canonical product** (needs Phase 5) and validated (price, dates, product) before it can appear in a comparison |
| Reviewed identity | A vendor's identity and business details are reviewed before any of their offers are published; offers can also be reviewed before going live |
| Three visible sources | Customers can tell where a price comes from: **scraped retailer listing**, **verified-vendor offer**, or **vendor-submitted (unreviewed, not published)** |
| Validity | Offers carry start and end dates and expire automatically; weekly deals are the default rhythm |
| Separate accounts | Vendor accounts are a separate system from customer accounts, not a flag on `users` |
| Audit trail | Changes to offers and review decisions are recorded |
| Business data | Business identification details (for example a GST number, to be decided) are sensitive; collect only what review needs and protect it |

**Dependencies:** Phase 5 (canonical products), Phase 4A (authentication and verified email), and an admin review tool.

**Design hooks to keep now:** when vendor offers arrive, price objects in API responses gain a `source` field so the frontend can label each price; `canonical_products` is already in the schema for the linkage.

---

### After Phase 5 and Phase 4A

- **Phase 6:** connect the React prototype to the API, with authentication.
- **Phase 7:** one pipeline command (open item 12) plus APScheduler, so price history builds up daily, watchlist price changes become meaningful and real price-drop deals become possible.
- **Phase 9:** vendor accounts, once matching and accounts exist.

Rules: mappings and brand aliases are explicit and reviewable (JSON files, not heuristics); unmapped, unknown and review values are reported, never silently guessed; raw, cleaned, normalized and branded layers stay untouched by later steps; `taxonomy.json` and `aliases.json` are versioned together; the loader never deletes listings; catalog and listing routes never write; matches are conservative and ambiguous cases are reported, not forced; deals and prices shown publicly must be verifiable from the data.
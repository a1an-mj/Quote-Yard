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
| 8 | [MyG Scraper](#8-current-myg-scraper) | 20 | [Current Status](#20-current-status) |
| 9 | [MyG Price Cleaning](#9-myg-price-cleaning) | 21 | [Hardest Parts](#21-hardest-parts) |
| 10 | [MyG Pagination](#10-myg-pagination) | 22 | [Final Goal](#22-what-quote-yard-should-eventually-do) |
| 11 | [MyG Edge Cases](#11-myg-navigation-edge-cases) | 23 | [Immediate Next Step](#23-immediate-next-step) |
| 12 | [Resource Mgmt / Oxygen / Pittappillil](#12-myg-resource-management) | | |

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

## 🛍️ **Main Product Categories**

| | | |
|---|---|---|
| Mobiles | Laptops / Desktops | Tablets |
| Accessories | TVs | Home & Kitchen |
| Refrigerators | Washing Machines | Air Conditioners |
| Small Appliances | Personal Care | Home Automation |

*Plus other retailer categories as needed.*

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

## 🧹 **3.2 Data Cleaning / Normalization**

Make data from different retailers consistent.

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

> Product matching stays **separate** from scraping.

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
├── data/
├── frontend/
├── scrapers/
├── tests/
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

Not a scraper bug, since Oxygen's site has two listings for the same product. Keep in mind for matching.

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
> ⚠️ **Open item:** the 55 subcategory URLs have not been individually spot-checked (Oxygen's mobiles slug needed correcting after a failed guess). Review the logs on the next full headless run to confirm every subcategory returns products rather than silently stopping at page 1.

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

Mobile data is considered **good enough for now**.

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
| **2** | **Data Processing** | Raw data → Cleaning → Normalization → Duplicate handling |
| **3** | **PostgreSQL** | Schema, SQLAlchemy models, retailer records, product records, listings, prices, price history |
| **4** | **FastAPI** | Product endpoints, search, product detail, comparison, price history |
| **5** | **Product Matching** | Match retailer listings into canonical products |
| **6** | **React Integration** | Connect frontend to FastAPI |
| **7** | **Scheduler** | Automate retailer scraping and DB updates |
| **8** | **Deployment** | Choose environment, move from development to a stable server |

---

# 20. **CURRENT STATUS**

## ✅ **Completed / substantially completed**

**General**

| | |
|---|---|
| Quote Yard concept | Technology direction |
| Repository setup | Git / GitHub setup |
| Frontend prototype direction | System Requirements + SRS spreadsheet |

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
- Category/subcategory grouping (5 main / 55 sub)
- Grouped JSON output · category and subcategory on every product

**Nandilath G Mart**: built and confirmed

- WordPress / WooCommerce storefront inspected
- Card selectors, name/URL, current/discounted price, availability confirmed
- Category/subcategory grouping · `/page/N/` pagination confirmed
- Full-page testing completed · duplicate URL protection
- Resource blocking · 403/404/5xx handling

> **Four retailers are active:** myG · Oxygen · Pittappillil · Nandilath G Mart
>
> **Croma is deferred.** The architecture must stay retailer-scalable so it can be added without changing the core normalization, database, backend or frontend design.

## 🚧 **Currently being finished**

Confirm the unified MyG scraper is robust end to end against:

| | |
|---|---|
| 403 | 404 *(fix applied; confirming run may still be needed)* |
| Resource exhaustion | Categories with different page counts |
| Missing availability | Navigation failures |

## 🔎 **Open items to verify**

| # | Item |
|:-:|------|
| 1 | **MyG TVs:** `CATEGORIES` in `myg_scraper.py` has no `tvs` entry, although TVs are listed as done. Confirm whether an earlier script scraped them or whether they still need adding. |
| 2 | **Oxygen naming:** listings are internally inconsistent and may contain near-duplicates. Relevant to normalization/matching. |
| 3 | **Oxygen out-of-stock path:** unverified, because the tested category had no out-of-stock products. |
| 4 | **Pittappillil subcategories:** the 55 URLs were not individually spot-checked (though the scraper runs end to end). |
| 5 | **Nandilath G Mart:** built and tested. Uses `.wd-product` cards, names/URLs from `.wd-entities-title a`, the discounted `<ins>` price when present, and `/page/N/` pagination. |

## ➡️ **Next major work**

The four scrapers are now the data-collection layer. **Do not add Croma yet.**

```
Four retailer raw data -> Data Cleaning -> Normalization -> Duplicate Handling -> PostgreSQL
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
Retailer Websites -> Scrapers -> Data Normalization -> Product Matching
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

MyG, Oxygen, Pittappillil and Nandilath G Mart are the four active retailers. **Croma is intentionally deferred.**

## ➡️ **Move to Phase 2: Data Processing**

```
Raw JSON from four retailers
        |
   Data Cleaning
        |
   Normalization
        |
   Duplicate Handling
        |
   PostgreSQL
```

**The common scraper output stays retailer-independent:**

```python
{
    "name": "...",
    "price": 39999,
    "url": "...",
    "availability": "In stock",
    "shop": "...",
    "category": "...",
    "subcategory": "..."
}
```

Retailer-specific HTML, selectors, pagination, price formats and availability logic stay **inside each scraper**. The downstream processing layer works against the common model, so future retailers such as Croma can be added without redesigning the system.

> 🛑 **Do not** make further scraper changes to MyG, Oxygen, Pittappillil or Nandilath G Mart unless a real bug or data-quality requirement appears. The next major focus is the **scalable data-processing layer**.
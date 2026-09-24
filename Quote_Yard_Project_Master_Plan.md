# Quote Yard — Project Master Plan

## 1. Project Overview

**Quote Yard** is a retail price comparison platform focused initially on Kerala/India retailers.

The system will collect product listings and prices from multiple retailers, normalize the data, store it in PostgreSQL, match equivalent products, and present price comparisons through a React frontend.

### Target retailers
- myG
- Oxygen
- Pittappillil
- TechQ
- Croma

### Main product categories
- Mobiles
- Laptops / desktops
- Tablets
- Accessories
- TVs
- Home & Kitchen
- Refrigerators
- Washing Machines
- Air Conditioners
- Small Appliances
- Personal Care
- Home Automation
- Other retailer categories as needed

---

## 2. Core Architecture

```text
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

A scheduler will trigger the scraping system automatically.

---

## 3. Major Modules

### 1. Scraping / Data Collection
Collect product information from each retailer.

Current common data model:

```text
name
price
url
availability
shop
category
```

The scraper should primarily collect what the retailer actually displays.

**Important decision:** Do not try to perfectly parse every product's RAM, storage, processor, color, etc. across every category. Retailer naming is inconsistent. Preserve reliable raw listing data first.

### 2. Data Cleaning / Normalization
Make data from different retailers consistent.

Examples:

```text
myG:
Samsung Galaxy S25 5G | 12 GB | 256 GB

Oxygen:
Samsung S25 12/256GB

Pittappillil:
SAMSUNG GALAXY S25 5G 256 GB
```

Eventually these need to be normalized so the system can determine whether they represent the same product/variant.

### 3. Product Matching
One of the hardest parts of Quote Yard.

The system must distinguish:

```text
Galaxy S25 256GB
Galaxy S25 Ultra 256GB
Galaxy S25 512GB
```

Possible matching signals:
- Brand
- Product/model name
- Model number
- Variant
- Storage
- RAM where applicable
- Color where reliable
- Category-specific identifiers

Product matching stays separate from scraping.

### 4. Database
Database: **PostgreSQL**

ORM: **SQLAlchemy**

Future concepts:

```text
Retailers
Products
Product Variants
Categories
Retailer Listings
Prices
Price History
```

Conceptually:

```text
Canonical Product
       |
       +---- myG listing
       +---- Oxygen listing
       +---- Pittappillil listing
       +---- TechQ listing
       +---- Croma listing
```

### 5. Backend
Technology: **FastAPI**

```text
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
```

Possible future endpoints:

```text
GET /products
GET /products/{id}
GET /products/{id}/prices
GET /search?q=samsung
GET /compare/{product_id}
```

### 6. Search
Initially simple database-backed search is enough.

```text
User → React → FastAPI → PostgreSQL → Results
```

Do not over-engineer search initially.

### 7. Comparison
Show equivalent products across retailers:

```text
Samsung Galaxy S25 256GB

myG           ₹39,999
Oxygen        ₹40,499
Pittappillil  ₹40,999
Croma         ₹41,999
```

This depends heavily on product matching.

### 8. Scheduler
Technology: **APScheduler**

Example:

```text
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

One retailer failing should not stop the whole update.

### 9. Frontend
Technology:
- React
- Vite
- Tailwind CSS / utility styling
- React Router

Prototype flow:

```text
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
```

---

## 4. Frontend Design

Visual direction:
- Terracotta primary
- Warm Ivory
- Warm Taupe
- Olive Green
- Walnut Brown
- Near Black

Approximate palette:

```text
Terracotta   #C65A3A
Warm Ivory   #F5EFE5
Warm Taupe   #A99B8D
Olive Green  #656A45
Walnut Brown #4A3025
Near Black   #171512
```

Style:
- Neo-brutalist / playful brutalist
- Bold chunky typography
- Rounded cards
- Strong dark framing
- High contrast
- Solid color blocks
- Subtle shadows
- Minimal gradients
- Mobile-first
- Responsive
- Subtle animations

---

## 5. Technology Stack

### Frontend
```text
React
Vite
Tailwind CSS
React Router
```

### Backend
```text
Python
FastAPI
SQLAlchemy
```

### Database
```text
PostgreSQL
```

### Scraping
```text
Python
Playwright
Chromium
```

### Scheduling
```text
APScheduler
```

### Development
```text
Git
GitHub
```

Deployment is not finalized yet. An Asus VivoBook may be used as an experimental/self-hosted server later.

---

## 6. Important Technology Decisions

### No OpenAI extraction
Quote Yard will **not use OpenAI AI extraction for scraping**.

Scraping uses deterministic techniques:
- Playwright
- CSS selectors
- DOM extraction
- normalization rules

### Avoid premature complexity
Do not add these for the MVP unless a real requirement appears:
- Kafka
- RabbitMQ
- Celery
- Redis
- Kubernetes
- complicated AI extraction
- complex search engines
- microservices

The MVP stack is:

```text
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
```

---

## 7. Current Repository

```text
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

Main unified MyG scraper:

```text
scrapers/myg_scraper.py
```

Data is stored under:

```text
data/
```

GitHub repository:

```text
git@github.com:a1an-mj/Quote-Yard.git
```

Main branch:

```text
main
```

---

## 8. Current MyG Scraper

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

Each category defines:
- `base_url`
- `output`
- `label`

Current selectors:

```python
PRODUCT_LINK_SELECTOR = "a.line-clamp-2"
PRICE_SELECTOR = '[id^="sec_discounted_price_"]'
AVAILABILITY_SELECTOR = "p.text-green"
```

Each product currently becomes:

```json
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

## 9. MyG Price Cleaning

Example:

```text
₹1,23,456.00
```

becomes:

```text
123456
```

`clean_price()` removes currency symbols, commas and spaces, then converts the value to an integer. Invalid values become `None`.

---

## 10. MyG Pagination

The scraper constructs direct URLs:

```text
Page 1:
https://www.myg.in/category/

Page 2:
https://www.myg.in/category/page-2/

Page 3:
https://www.myg.in/category/page-3/
```

It does **not** click pagination buttons.

This is intentional because the website's pagination behavior can differ from direct page navigation.

Safety limit:

```python
SAFETY_MAX_PAGES = 100
```

---

## 11. MyG Navigation Edge Cases

### 403

Some pages can return:

```text
403 Forbidden
```

Example encountered:

```text
/mobile-phones/page-10/
```

The scraper should stop that category cleanly.

### 404

Some categories have fewer pages.

Example:

```text
/home-automation/page-3/
```

does not exist.

The current fix should check the HTTP response before calling the product selector:

```python
response = page.goto(url, wait_until="domcontentloaded")

if response and response.status == 404:
    log.warning("Page does not exist (404). Stopping category.")
    break

if response and response.status == 403:
    log.warning("MyG returned 403 Forbidden. Stopping category.")
    break
```

This preserves already-collected products and allows them to be saved.

---

## 12. MyG Resource Management

A major issue encountered was:

```text
ERR_INSUFFICIENT_RESOURCES
```

The actual page could be opened normally in Firefox, so the page itself was valid. The problem was likely Chromium resource usage during a long scrape.

Current strategy:

### Block unnecessary resources

```python
BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
```

The current JSON does not need these resources.

### Fresh page per category

Current architecture:

```text
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
```

This avoids keeping every category page alive.

A new browser is not required for every category.

---

## 13. MyG Scraper Commands

All categories:

```bash
python scrapers/myg_scraper.py
```

Headless:

```bash
python scrapers/myg_scraper.py --headless
```

Selected categories:

```bash
python scrapers/myg_scraper.py --only mobiles tablets
```

One category:

```bash
python scrapers/myg_scraper.py --only home-automation
```

Page safety limit:

```bash
python scrapers/myg_scraper.py --max-pages 20
```

---

## 14. Existing MyG Work

### Mobiles
Previously collected approximately 108 products before encountering a 403 at page 10.

Mobile parsing extracted:
- RAM
- Storage
- Color

Some feature phones legitimately had no normal RAM field.

Important discovery:
product names and URLs can disagree on variants/colors/storage.

**Displayed product name is more trustworthy for variant information than blindly deriving information from URLs.**

Mobile data is considered good enough for now.

### Laptops
Laptop names were inconsistent, especially Apple products, gaming laptops and desktop/AIO listings.

A processor parser was improved and tested with examples such as:

```text
AMD Ryzen 7
AMD Ryzen 5
Intel Core i3
Intel Core i5
Intel Core Ultra 5 225H
M5 Pro Chip
Intel Core i7 14700HX
AMD Ryzen 7 7735HS
```

Laptop parsing is considered good enough for now.

### Tablets
Use the simple listing approach:

```python
name = product["name"].split("|")[0].strip()
```

Keep:
- name
- price
- url
- availability
- shop
- category

Duplicate listings and missing availability were observed and are not being over-engineered yet.

### TVs
Same simple approach.

### Accessories
Same simple approach.

---

## 15. Product Parsing Strategy Going Forward

For new categories:

**Do not over-parse specifications.**

Prefer:

```text
Raw listing
   ↓
name
price
url
availability
shop
category
```

Only add category-specific parsing when there is a real requirement.

This prevents inconsistent retailer naming from making the project unnecessarily complicated.

---

## 16. JSON Saving

Current saving behavior **replaces** the existing JSON snapshot.

It does not append.

Example:

```text
Old:
Phone A
Phone B

New scrape:
Phone A
Phone C
```

Result:

```text
Phone A
Phone C
```

This is intentional for the current snapshot stage.

Later, PostgreSQL will store price history separately.

---

## 17. Debugging Rule

Always debug in this order:

```text
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
```

Do not change multiple unrelated things before testing.

Use **one test** for each change.

This makes it clear what actually solved the issue.

---

## 18. Development Environment

Current environment:

```text
Arch Linux
Python 3.14.6
.venv
Playwright
Chromium
```

Playwright reported that Arch Linux was not officially supported and downloaded a fallback Ubuntu 24.04 Chromium build, but the browser works.

A previous Python file named `inspect.py` shadowed Python's standard-library `inspect` module. It was renamed to:

```text
inspect_page.py
```

---

## 19. Implementation Roadmap

### Phase 1 — Data Collection

```text
MyG
  ↓
Oxygen
  ↓
Pittappillil
  ↓
TechQ
  ↓
Croma
```

Build and stabilize each scraper.

### Phase 2 — Data Processing

```text
Raw data
   ↓
Cleaning
   ↓
Normalization
   ↓
Duplicate handling
```

### Phase 3 — PostgreSQL

Build:
- schema
- SQLAlchemy models
- retailer records
- product records
- listings
- prices
- price history

### Phase 4 — FastAPI

Build:
- product endpoints
- search
- product detail
- comparison
- price history

### Phase 5 — Product Matching

Match retailer listings into canonical products.

### Phase 6 — React Integration

Connect frontend to FastAPI.

### Phase 7 — Scheduler

Automate retailer scraping and database updates.

### Phase 8 — Deployment

Choose deployment environment and move the application from development to a stable server.

---

## 20. Current Status

### Completed / substantially completed
- Quote Yard concept
- Technology direction
- Repository setup
- Git/GitHub setup
- MyG scraping architecture
- Mobile scraping
- Laptop scraping
- Tablet scraping
- TV scraping
- Accessories pipeline
- Basic Home & Kitchen scraping
- Resource blocking
- Fresh page per category
- 403 handling
- Identification of 404 pagination issue
- Simple raw-listing strategy
- Frontend prototype direction
- System Requirements + SRS documentation spreadsheet

### Currently being finished
Make the unified MyG scraper robust against:
- 403
- 404
- resource exhaustion
- categories with different page counts
- missing availability
- navigation failures

### Next major work
After MyG is stable:

```text
Oxygen
  ↓
Pittappillil
  ↓
TechQ
  ↓
Croma
  ↓
PostgreSQL
```

---

## 21. Hardest Parts

The main difficult areas are expected to be:

### Product matching
Determining whether different retailer listings represent the same product/variant.

### Reliable multi-retailer scraping
Every retailer has different HTML, pagination, price formats, availability, and anti-bot behavior.

### Database design
Supporting canonical products, retailer listings, variants, current prices and historical prices.

### Data quality
Handling duplicates, missing values, inconsistent names, changed URLs and temporary failures.

### Automation
Allowing one retailer to fail without stopping the entire update process.

---

## 22. What Quote Yard Should Eventually Do

```text
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
```

Example final experience:

```text
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
```

The goal is to build a working end-to-end price comparison system first, then progressively improve matching, data quality, automation and UX.

---

## 23. Immediate Next Step

Current error:

```text
Home Automation - PAGE 3
Timeout waiting for a.line-clamp-2
```

Cause:

```text
/home-automation/page-3/
```

does not exist.

Next change should be **only** the 404 response check:

```python
response = page.goto(url, wait_until="domcontentloaded")

if response and response.status == 404:
    log.warning("Page does not exist (404). Stopping category.")
    break

if response and response.status == 403:
    log.warning("MyG returned 403 Forbidden. Stopping category.")
    break
```

Then test once:

```bash
python scrapers/myg_scraper.py --only home-automation
```

Do not make additional scraper changes until this test is complete.

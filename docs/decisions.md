# Design decisions

How each stage works, why, and the numbers it produced on the first full
data set (2,975 scraped records from 38 files). Stages are separate: none of
them changes the output of an earlier one.

## Common listing model

Every scraper emits `name`, `price` (integer rupees), `url`, `availability`,
`shop`, `category`, and `subcategory` where the retailer has one. Names are
kept exactly as the retailer shows them; specs are not parsed at scrape
time. Saving a scrape **replaces** the JSON snapshot; history lives in
PostgreSQL. The displayed name is more reliable for variants than the URL
(they can disagree).

## Cleaning (`data_processing/cleaner.py`)

`data/` -> `cleaned_data/` + `reports/cleaning_report.json`

- Validates required fields, positive integer price, http(s) URL; trims whitespace.
- Missing availability becomes `Unknown`, never `Out of stock`: it means the scraper could not tell.
- Keeps names, subcategories (no inventing) and duplicate URLs (flagged, not removed).
- Stamps every record with `scraped_at`, the raw file's modification time: when the scraper saw it. A file that was not re-scraped (myG TVs) or that the pipeline restored keeps its old time.

Result: 2,975 / 2,975 clean, 0 errors; 2,796 In stock, 179 Unknown. 10
duplicate URL groups, all Nandilath products listed under two subcategories
(a soundbar under Home Theater and Sound Bars), so deduping by URL would
lose category data. Per retailer: myG 1,103 · Nandilath 749 · Oxygen 245 ·
Pittappillil 878.

## Normalization (`data_processing/normalizer.py`, `taxonomy/`)

Maps each retailer's categories onto Quote Yard's own taxonomy
(`taxonomy.json`: 14 categories, 48 product types; `aliases.json`: 113
mappings). The database never depends on retailer category names.

- **Key is `(retailer, raw_category, raw_subcategory)`**, because retailer categories are navigation, not product types (Pittappillil "Mobiles, Laptops and More" holds phones, laptops and watches). A missing subcategory uses the key `__none__`.
- **Product type first, parent derived**: type names are unique, so the parent is looked up from the type.
- **Explicit mappings only**, casefolded. No plural-stripping heuristics.
- **Status per row**: `mapped` (type known), `parent_only` (category known, type null), `unmapped` (mixed bucket, both null). Unknown tuples raise `MappingError`, the run fails and the previous output is kept (written via a `.tmp` swap).
- One type per big appliance (Refrigerator, Washing Machine, Television, Mobile Phone); door style, load type and so on are attributes for later. Genuinely different products stay separate (Washer Dryer, Chest Freezer, each fan type).
- `taxonomy.json` `version` must equal `aliases.json` `taxonomy_version`, or the normalizer refuses to load. Bump both together.
- Raw values are kept next to canonical ones, so a mapping can be redone without re-scraping.

Result: 2,389 mapped (80%), 346 `parent_only`, 240 `unmapped`. Accepted
for the MVP; see roadmap issue 5. 30 of 48 types appear at 2+ retailers.

## Brand extraction (`data_processing/brand_extractor.py`, `brands.json`)

Adds `brand`, `brand_status` (`matched` / `unknown` / `review`) and
`brand_candidates`.

- Whole-token matching on the casefolded name; a match inside a longer match is dropped ("Prestige" inside "TTK Prestige").
- Two or more different brands -> `review` with the candidates listed; never a guess.
- `start_only` brands match only as the first word (HP, Nothing, Vu, Noise, Urban, Google, Apple, Sharp, Lifelong): "1.5 HP" is an AC rating, "Google TV" is software. Google alone removed 93 false conflicts.
- Xiaomi, Redmi, Mi and Poco are one brand; the line stays in the name.
- Aliases fix retailer typos explicitly (`Bosch` <- "B0SCH", `V-Guard` <- "V-GURAD"). Duplicate aliases fail at load time.
- `brands.json` `version` (now 1.1) is stored on every listing; bump it with every edit.

Result: 2,942 matched, 10 review, 23 unknown (98.9%). Known limit: it reads
the name only, so "Spigen case for Samsung Galaxy" is tagged Samsung.

## Database (`db/`)

```
retailers 1--< listings 1--< listing_categories
                   |--< price_history
                   >-- canonical_products (nullable)
```

- `listings`: one row per `(retailer_id, url)`. Integer rupees, `> 0`. Availability limited to `In stock` / `Out of stock` / `Unknown`. Checks: `matched` exactly when `brand` is set; `review` exactly when `brand_candidates` is set.
- `listing_categories`: one row per distinct raw pair per listing, unique on `(listing_id, raw_category, COALESCE(raw_subcategory, ''))`. Keyed on the raw pair, not the canonical type, because Home Theater and Sound Bars both map to Soundbar and the provenance would be lost.
- `category` / `product_type` are plain text, not lookup tables; the JSON taxonomy is the source of truth and `taxonomy_version` tracks drift.
- Schema changes are Alembic migrations (`db/migrations/`). A new database is built by `create_all` and stamped at the head.

**Loader rules** (`db/loader.py`): validate everything first, one
transaction; files in sorted order, first record per `(shop, url)` wins;
price history on first sighting, any price change, or a known availability
that differs from the last known one (`Unknown` is never a change);
`last_seen_at` is the record's `scraped_at`, not the load time (duplicates keep the latest); never
delete listings (myG truncation would make them look removed); idempotent;
`--dry-run`.

## API (`api/`)

Read-only, under `/api/v1`, docs at `/api/v1/docs`.

| Endpoint | Purpose |
|----------|---------|
| `/health` | API and database check |
| `/retailers`, `/product-types`, `/brands` | Catalog with counts |
| `/listings` | Search (`q`: every word must appear, `ILIKE`, input escaped) and filters: retailer, category, product_type, brand, price range, availability, `seen_since`; sort `price_asc` / `price_desc` / `name`; `limit` <= 100 |
| `/listings/summary` | Per-retailer count, min/max and cheapest for the same filters. Interim: it does not claim the listings are the same product |
| `/listings/{id}`, `/listings/{id}/prices` | Detail and price history |
| `/products` | Matched products: `q` (every word in name, brand or model), brand, category, product_type, price range on the lowest price, `min_retailers` (2 = comparable only); sort `name` / `price_asc` / `price_desc` / `retailers`. Each with listing and retailer counts and min/max price. Products without listings are hidden. |
| `/products/{id}`, `/products/{id}/prices` | Specs plus every offer (retailer, price, availability, `box_note`, URL, `last_seen_at`), cheapest first; price history per listing |
| `/compare/{id}` | Best offer per retailer, cheapest first; `cheapest_listed` on every tie; `spread` between the listed retailers; `not_listed` = tracked retailers with no match in our data |

- Category filters use `EXISTS`, not `JOIN` (10 listings have two category rows). Every sort adds `id` as a tie-breaker.
- `/listings/summary` is declared before `/listings/{id}`; ids outside 32-bit return 422.
- **Current offers only** (`api/freshness.py`): a listing counts when it was seen in its retailer's latest scrape (within 6 hours of that retailer's newest sighting) and that scrape is under 3 days old. Product counts, prices, the product list, `min_retailers` and `/compare` use current listings only; `/products/{id}` still lists old offers with `current: false`. A product with no current listing drops out of `/products`. First applied 2026-10-30: 36 products comparable across retailers (46 before, 10 of them only through offers missing from the latest scrape).
- Products: an `Out of stock` listing never sets a product's price range or wins a comparison; within a retailer the best offer is the cheapest buyable one. `spread` is null with fewer than two buyable offers. `not_listed` means "not found in our data", never "not sold there".
- Protection: `default_transaction_read_only=on` on the API engine, 5 s `statement_timeout`, `q` <= 100 chars / 8 words, GET-only CORS, in-process sliding-window rate limit (`api/ratelimit.py`, per process, `/health` exempt, 429 with `Retry-After`).

## Matching (`matching/`, `db/match_writer.py`)

Phones first: the largest overlap (277 listings at all four shops), and the
names carry brand, model, RAM and storage in four different formats.

**Key:** `(brand, model, network, RAM, storage, package)`. Colour is never
in the key. Rules (`matching_version` 1.1):

- Only `brand_status: matched` listings take part.
- Model = name head (before `|`, `(` or the first size), casefolded, brand and filler words removed, spaces removed (`V70FE` = `V70 FE`). For Samsung "galaxy" is optional (Nandilath omits it). `Phone (4a)` reads as `4a`.
- Variant words keep models apart (S26 vs S26 Ultra, Note 17 vs Note 17 Pro, 16 vs 16 Pro+).
- Network from the whole name, `LTE` = 4G. A listing without one joins its model's network if only one is seen; if the model exists as both 4G and 5G it goes to review (Galaxy A07 LTE vs A07 5G).
- Bundles ("photographer kit") are part of the key. Box contents ("without adapter") are not: the listing merges and keeps `box_note`.
- Retailer-specific words are dropped only when verified against the retailer's own spec table, and only straight after the brand. Pittappillil "SMART": its Model field reads `4B 5G` for "NOTHING SMART 4B 5G" and `G06 POWER 4G` for "MOTOROLA SMART G06 POWER 4G" (checked 2026-10-29). "smart" is not a global filler word.
- Apple ignores RAM. Phones with no RAM and storage match on brand + `TA-xxxx` code.
- A group whose price spread is over 25% is kept but flagged.

**Writing** (`python -m db.match_writer [--dry-run]`): reads in-scope
listings from the database, runs the matcher, upserts `canonical_products`
by `match_key`, sets `canonical_product_id` and `box_note`, one transaction.
Products are never deleted (orphans are reported) so ids stay stable.
Unmatched in-scope listings are unlinked; other types are never touched.
The loader never touches the links, so run the writer after every load.

**Verified:** all 32 cross-retailer groups checked by hand, 0 wrong
matches; reruns change nothing; SQL cross-check finds 0 non-phone links and
0 brand mismatches.

## Frontend

React, Vite, Tailwind, React Router. Neo-brutalist: bold chunky type,
rounded cards, strong dark framing, solid colour blocks, high contrast,
mobile first, subtle animation.

| Colour | Hex |
|--------|-----|
| Terracotta (primary) | `#C65A3A` |
| Warm Ivory | `#F5EFE5` |
| Warm Taupe | `#A99B8D` |
| Olive Green | `#656A45` |
| Walnut Brown | `#4A3025` |
| Near Black | `#171512` |

## Technology choices

React + FastAPI + PostgreSQL (SQLAlchemy 2, psycopg 3, Alembic) +
Playwright + APScheduler (planned). Deterministic scraping (selectors, DOM),
no AI extraction. No Kafka, RabbitMQ, Celery, Redis, Kubernetes, search
engines or microservices until a real requirement appears. Search is plain
`ILIKE` over about 3,000 rows; add `pg_trgm` if it gets slow.

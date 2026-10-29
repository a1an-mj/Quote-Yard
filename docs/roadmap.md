# Roadmap

Last updated 2026-10-29.

## Where we are

| Stage | State |
|-------|-------|
| Scrapers (4 retailers) | ✅ Working. myG is capped at 108 records in 8 of 11 categories (issue 1). Croma deferred. |
| Cleaning, normalization, brand extraction | ✅ 2,975 records; 80% fully mapped to a product type; 98.9% brand matched |
| PostgreSQL + loader | ✅ 2,965 listings, idempotent loads, price history (one point per listing so far) |
| Read-only API | ✅ `/api/v1`: listings search, per-retailer summary, detail, price history, catalog |
| Matching | 🟡 **Phones only**: 277 listings, 113 products, 32 at 2+ retailers, 0 wrong matches on a full hand check. Written to the database. About 9% of all listings are covered. |
| Test isolation | ✅ Tests use `quote_yard_test`, never the real database |
| React frontend | ⬜ Prototype exists, not connected |
| Scheduler | ⬜ Not started; there is no single pipeline command yet |
| Accounts | ⬜ Designed ([`accounts-and-vendors.md`](accounts-and-vendors.md)), not started |

## Next, in order

The order puts working price comparison in front of users before accounts,
and gets price history growing early, since deals and alerts depend on it.

### 1. Product API (finishes matching for phones)

- `GET /products`: search and filter canonical products (brand, product type, price range), each with offer count, retailer count, min/max price.
- `GET /products/{id}`: the product plus every linked listing (retailer, price, availability, `box_note`, `last_seen_at`, URL).
- `GET /products/{id}/prices`: price history of its listings.
- `GET /compare/{id}`: one row per retailer, cheapest listing first. "Cheapest" only as "cheapest of the retailers listed".
- Products whose listings are all gone (orphans) are hidden. Box notes are shown next to the price.
- Read-only connection, same caps and rate limit as the listing routes.

### 2. One pipeline command, then the scheduler

- `python -m pipeline` (or similar): scrape -> clean -> normalize -> brand -> load -> match, one retailer failing does not stop the others, a summary at the end.
- Then APScheduler (daily, about 02:00) so `price_history` grows. Without it there is no price-drop data.
- Re-check stale prices: Pittappillil's site showed the Motorola G06 Power at 13,999 while our data has 15,999.

### 3. Connect the React frontend

- Search over products (matched) and listings (unmatched), product page with the comparison table and price history.
- Unmatched categories use `/listings/summary`, labelled "per retailer, not matched products".
- Visual direction is in [`decisions.md`](decisions.md#frontend).

### 4. Coverage

- myG 108-record cap (issue 1).
- Matching for the next types. TVs, refrigerators, washing machines, ACs and laptops usually carry a manufacturer model code, which is a stronger key than phone names. When the second type is added, split the shared matcher core (brand gate, key, review report, writer) from the phone rules; not before.
- Normalization coverage: 20% of records are `parent_only` / `unmapped` (issue 5).

### 5. Accounts, watchlist, deals

Designed in [`accounts-and-vendors.md`](accounts-and-vendors.md). **Open decision:**
the current design puts the whole site behind login. A comparison site is
found through search engines and shared links, which a login wall blocks,
and free sign-up barely slows scrapers (rate limits do that). Recommendation:
keep browsing and comparison public; require an account for the watchlist
and alerts.

### 6. Deployment

Choose the host (an Asus VivoBook as a self-hosted server is an option).
Use a SELECT-only database role for the API and a separate role for the
writers. Behind a reverse proxy, run uvicorn with `--proxy-headers
--forwarded-allow-ips=<proxy>` so the rate limiter sees real clients.

### Later

- Vendor accounts and local shop offers ([`accounts-and-vendors.md`](accounts-and-vendors.md#vendors)).
- Croma, through the same scraper interface.

## Open issues

| # | Issue | Notes |
|:-:|-------|-------|
| 1 | **myG truncation** | 8 of 11 categories have exactly 108 records (9 pages x 12), matching a 403 at page 10. Cause unknown. Test one at a time: open pages 9-11 in a normal browser; run `--only mobiles --max-pages 12`; check whether sorting or filters expose other products. Read `robots.txt` and the terms first. Do not spoof headers or rotate identities; if the cap is deliberate, ask myG for a feed. Until fixed, no "cheapest" claim where myG coverage could change the answer. |
| 2 | **myG TVs not in the scraper config** | The data has a myG `TV` category (108 records) but `CATEGORIES` in `myg_scraper.py` has no TV entry. A re-scrape would lose them. |
| 3 | **Out-of-stock path untested** | Data has only `In stock` (2,796) and `Unknown` (179). Schema and loader allow `Out of stock`; nothing has exercised it end to end. |
| 4 | **Pittappillil: 7 empty subcategories** | 55 configured, 48 present in the data. Confirm they are really empty, not a silent scraper stop. |
| 5 | **Unmapped records (20%)** | 346 `parent_only`, 240 `unmapped`. Cheapest wins: an `Earbuds` type (Oxygen Gadgets, 23); a name-rule layer (`mapping_status: rule_mapped`, versioned) for mixed buckets such as Pittappillil Chimney & Hob. |
| 6 | **Brand review records (10)** | Faber + LG (4, real ambiguity), Eureka Forbes + Aquaguard (4), Samsung + Symphony (2). Resolve by hand or a `same_company` rule. Optional brand batch: Hykon, Vidiem, Everest, Kuhl, Fingers, Indus Valley, Aquaneeta, `Blueberry` <- "blueberrys". |
| 7 | **Cleaning validator never fails** | 0 errors on real data. Check it can reject bad input; add per-category price warnings (not a flat ceiling). |
| 8 | **Loader URL-origin warning** | Proposed: warn when a URL does not start with its retailer's `base_url`. |
| 9 | **Repo leftovers** | `tests/test.py` is a Playwright scratch script (move to `scrapers/` or delete); `frontend/src/{components,pages,context,data}` is a stray folder from a brace-expansion `mkdir`. |

## Done (summary)

| When | What |
|------|------|
| Phase 1 | Scrapers for myG, Oxygen, Pittappillil, Nandilath G Mart |
| Phase 2 | Cleaning (2A), normalization with taxonomy v1.0 (2B), brand extraction with brands v1.1 (2C) |
| Phase 3 | PostgreSQL schema, loader, price history |
| Phase 4 | Read-only FastAPI with filters, summary, protection (timeout, caps, CORS, rate limit) |
| Phase 5 (phones) | Extraction report, matcher v1.1, Alembic + migration `0001`, match writer; 32 cross-retailer products |
| 2026-10-29 | `data/` removed from git (history still contains it); tests moved to `quote_yard_test`; this plan replaced `Quote_Yard_Project_Master_Plan.md` |

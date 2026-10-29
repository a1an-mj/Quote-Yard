# Scrapers

One Playwright script per retailer in `scrapers/`, all writing the common
listing model (see [`decisions.md`](decisions.md#common-listing-model)) to
`data/<retailer>_<category>.json`. Each run **replaces** the file for the
categories it scrapes.

Shared defensive behaviour: pages are opened by direct URL (never by
clicking pagination), a safety cap of 100 pages, images / media / fonts
blocked, a fresh page or context per category (avoids Chromium's
`ERR_INSUFFICIENT_RESOURCES` on long runs), and 403 / 404 stop the category
cleanly so products already collected are still saved. A page that does not load (timeout, `net::` error) is retried once after 5 seconds (`scrapers/navigation.py`); HTTP errors are never retried. Oxygen,
Pittappillil and Nandilath also stop on 5xx, wrap each page in try/except,
and stop when a page brings no new URLs.

Playwright warns that Arch Linux is unsupported and downloads an Ubuntu
24.04 Chromium build; it works. `scrapers/inspect_page.py` is a debugging
helper (renamed from `inspect.py`, which shadowed the standard library).

## myG (`myg_scraper.py`)

Custom storefront. 11 categories in `CATEGORIES` (each `base_url`,
`output`, `label`). Pagination `/category/page-N/`.

```python
PRODUCT_LINK_SELECTOR = "a.line-clamp-2"
PRICE_SELECTOR = '[id^="sec_discounted_price_"]'
AVAILABILITY_SELECTOR = "p.text-green"
```

Prices like `₹1,23,456.00` -> `123456`; unparseable -> `None`.

Known problems: page 10 returns **403**, so 8 categories stop at 108
records (roadmap issue 1); the data has a myG TV category but `CATEGORIES`
has no TV entry (issue 2). 404 on short categories (e.g. Home Automation
page 3) is handled; before that fix the crash lost earlier pages. If a
missing page ever returns 200 with an empty grid, catch the selector
timeout in `scrape_page()` and return an empty list.

```
python scrapers/myg_scraper.py [--headless] [--only mobiles tablets] [--max-pages 20]
```

## Oxygen (`oxygen_scraper.py`)

Shopify. Pagination `?page=N`. Data comes from `data-*` attributes on
`div.custom-product-card` (`data-product-title`, `data-product-price`,
`data-product-url`). **Prices are in paise**: divide by 100. 11 categories,
all verified on a full headless run; the phone collection slug is
`/collections/mobile-smart-phones`.

Availability is read from card text ("out of stock", "sold out", "add to
cart") with a per-button fallback. The site had nothing out of stock to
test against.

Naming is inconsistent even within Oxygen (`(Black, 128 GB) (6 GB RAM)` vs
myG-style pipes), and the same phone can appear under two slugs
(`vivo-v70-fe-...` and `vivo-v70fe-...`); the matcher handles both.

```
python scrapers/oxygen_scraper.py [--headless] [--only mobiles laptops] [--max-pages 1]
```

## Pittappillil (`pittappillil_scraper.py`)

Pagination `/stores/Mobile?page=N&limit=12`. Selectors:
`.products-list__item`, `.product-card__name a`, `.product-card__prices`,
`.product-card__availability span`.

The price block holds the current price and a struck-through original;
`extract_current_price()` reads only the direct text node.

`CATEGORIES` is two levels: 5 main categories (one output file each) with
55 subcategories, and every product carries both `category` and
`subcategory`. Only 48 subcategories appear in the data (roadmap issue 4).

Names add "SMART" after the brand for some phones (Motorola, Nothing); the
product spec table's Model field does not include it.

```
python scrapers/pittappillil_scraper.py [--headless] [--only kitchen-appliances] \
    [--subcategories mobiles] [--max-pages 1]
```

## Nandilath G Mart (`nandilath_scraper.py`)

WordPress / WooCommerce (Woodmart theme). Pagination `/page/N/`. Cards
`.wd-product`, name and URL from `.wd-entities-title a`. Price: the
discounted `.price ins ... bdi` when present, otherwise the normal price.
Category + subcategory like Pittappillil. Some products appear under two
subcategories with the same URL; the loader keeps one listing with two
category rows.

```
python scrapers/nandilath_scraper.py [--headless] [--only ...] [--subcategories ...] [--max-pages N]
```

## Adding a retailer

Same output model and the same defensive behaviour; add the shop to
`RETAILERS` in `db/create_tables.py` (with its `base_url`) and its
category tuples to `data_processing/taxonomy/aliases.json`. The normalizer
fails loudly on any tuple it does not know, which is the checklist.
Respect `robots.txt` and the site's terms; never spoof headers or rotate
identities to get past a block.

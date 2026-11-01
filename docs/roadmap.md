# Roadmap

Last updated 2026-11-01.

## Where we are

| Stage | State |
|-------|-------|
| Scrapers (4 retailers) | ✅ Working. myG is capped at 108 records in 8 of 11 categories (issue 1). Croma deferred. |
| Cleaning, normalization, brand extraction | ✅ |
| PostgreSQL + loader | ✅ 3,854 listings, 4,263 price-history rows |
| Data API | ✅ `/api/v1`: listings, products, compare, catalog; read-only, and login required since 2026-10-31 |
| Matching | 🟡 Phones and TVs (model codes, `matching/code_matcher.py`). Washing machines, fridges, ACs and microwaves next. |
| Pipeline and schedule | ✅ Running on the VivoBook; first scheduled run passed 2026-11-01 (02:14, 32 minutes, all stages OK) |
| Accounts backend | ✅ Sign-up, email codes, login, logout, forgot password |
| Saved items, alerts, deals | ✅ API built; alert emails go through the pipeline's last stage |
| React frontend | ✅ Rebuilt from the new design, on the real API |

## Next, in order

Accounts come before the frontend because the platform requires a login, so
no page is built against fake sessions.

### Phase 6: Pipeline and scheduler ✅

- ✅ `python -m pipeline`: scrape -> clean -> normalize -> brand -> load -> match. One retailer failing does not stop the others; empty or broken scrapes are restored from a backup; one run at a time; exit codes for the scheduler. 13 tests.
- ✅ Comparisons use current offers only: `last_seen_at` comes from the scrape time, and `/products` / `/compare` count only listings from each retailer's latest, recent scrape.
- ✅ Oxygen's `BRAND:SMART PHONES:MODEL 6/128 ...` names are matched (matching 1.2): 4 more cross-retailer products, unmatched phones 13 -> 7.
- ✅ Small fixes: `Blueberry` is `start_only` (a Samsung colour was read as a brand) and `blueberrys` an alias (brands 1.3); every scraper retries a page that did not load once (`scrapers/navigation.py`).
- ✅ Daily schedule: a systemd user timer runs `python -m pipeline` at 02:00 IST (`deploy/install-scheduler.sh`). Tested under systemd on the dev laptop, then removed there: the scheduled runs will be verified on the **Asus VivoBook**, the planned server.
- **VivoBook setup** (Ubuntu 24.04.5). This laptop stays the dev machine and runs Claude Code; the VivoBook is only the server, managed over SSH.
  1. PostgreSQL 18 or newer from PostgreSQL's own apt repository (24.04 ships 16, which cannot restore the laptop's dump), the system Python 3.12, git; `openssh-server`; clone the repo.
  2. `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/playwright install --with-deps chromium`
  3. Make a fresh transfer file on the laptop (`pg_dump -Fc` plus a `tar` of `data/`, which keeps the file times that decide which offers are current). **Restore the dump; do not create an empty database**: price history and product ids exist only there.
  4. `createdb quote_yard && pg_restore --no-owner -d quote_yard quote_yard.dump`, extract `data/`, then `.venv/bin/alembic upgrade head`.
  5. `.venv/bin/python -m pipeline --skip-scrape --dry-run`, then one full `python -m pipeline` by hand.
  6. `deploy/install-scheduler.sh` and `loginctl enable-linger $USER` (runs without a login session). Set lid-close to not suspend.
  7. Next morning: `journalctl --user -u quote-yard-pipeline -e` and `systemctl --user list-timers`. From then on the VivoBook holds the live data.
- Re-check stale prices: Pittappillil's site showed the Motorola G06 Power at 13,999 while our data has 15,999.

### Phase 7: Accounts, saved items, alerts, deals

- ✅ Accounts backend: see [`accounts-and-vendors.md`](accounts-and-vendors.md). SMTP sending is written but not yet tried with a real mailbox.
- ✅ Saved items and one alert type ("email me when the lowest price drops below X"). The pipeline's last stage, **alerts**, runs after match, so a mail failure cannot undo the price update.
- ✅ `/public/deals` for the landing page carousel.
- ✅ `/products/{id}/variants` and `/products?sort=newest` for the variant selector and "recently added".
- **Before the first real alert:** the scheduled service needs the SMTP settings; with the default console backend, alert emails only go to the log. Real sending is still untried.

### Phase 8: React frontend

Rebuild from the Claude Design artifact "Quote Yard" (minimal style, see [`decisions.md`](decisions.md#frontend)).

- Public: landing page with what the site does, the 4 retailers and today's deals.
- ✅ Landing page, against the real API, in light and dark.
- ✅ Sign up, verify email, log in, forgot password. `/home` is a placeholder until the logged-in pages exist.
- ✅ Home, Search with suggestions, Results, Product with its prices and history, Categories, Saved items & alerts.

### Phase 9: Coverage

- ✅ TVs matched on model codes (`python -m matching.code_matcher --type Television` writes a report).
- Next, one type at a time with a report first: washing machines, refrigerators, ACs, microwaves. A trial on exact codes found few or no cross-store matches for mixer grinders, ceiling fans and laptops.
- Normalization coverage: about 20% of records are `parent_only` / `unmapped` (issue 5).

### Phase 10: Deployment

Host on the Asus VivoBook. Public access and HTTPS. Set the email settings in the server's environment. Use a SELECT-only database role for the data API and a separate role for the writers. Behind a reverse proxy, run uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy>` so the rate limiters see real clients.

**Phases 6 to 10 complete the first release.**

### After the first release

- **Phase 11: myG 108-record cap** (issue 1), if it can be fixed within the site's rules. Confirmed again on the first pipeline run (2026-10-29): every myG category stopped at a 403 on page 10.
- **Phase 12: Vendor system**: shop accounts and local offers next to scraped prices ([`accounts-and-vendors.md`](accounts-and-vendors.md#vendors)). Needs accounts (Phase 7).

### Later

- Croma, through the same scraper interface.

## Open issues

| # | Issue | Notes |
|:-:|-------|-------|
| 1 | **myG truncation** | 8 of 11 categories have exactly 108 records (9 pages x 12), matching a 403 at page 10. Cause unknown. Test one at a time: open pages 9-11 in a normal browser; run `--only mobiles --max-pages 12`; check whether sorting or filters expose other products. Read `robots.txt` and the terms first. Do not spoof headers or rotate identities; if the cap is deliberate, ask myG for a feed. Until fixed, no "cheapest" claim where myG coverage could change the answer. |
| 2 | ~~**myG TVs**~~ | ✅ Added back to the scraper (`tvs`, 2026-11-01). |
| 3 | ~~**Out-of-stock path**~~ | ✅ Real data now has it (127 records on 2026-11-01) and the run loaded them. |
| 4 | **Pittappillil: 7 empty subcategories** | 55 configured, 48 present in the data. Confirm they are really empty, not a silent scraper stop. |
| 5 | **Unmapped records (20%)** | 346 `parent_only`, 240 `unmapped`. Cheapest wins: an `Earbuds` type (Oxygen Gadgets, 23); a name-rule layer (`mapping_status: rule_mapped`, versioned) for mixed buckets such as Pittappillil Chimney & Hob. |
| 6 | **Brand review records (10)** | Faber + LG (4, real ambiguity), Eureka Forbes + Aquaguard (4), Samsung + Symphony (2). Resolve by hand or a `same_company` rule. Optional brand batch: Hykon, Vidiem, Everest, Kuhl, Fingers, Indus Valley, Aquaneeta, `Blueberry` <- "blueberrys". |
| 7 | **Cleaning validator never fails** | 0 errors on real data. Check it can reject bad input; add per-category price warnings (not a flat ceiling). |
| 8 | **Loader URL-origin warning** | Proposed: warn when a URL does not start with its retailer's `base_url`. |

## Done (summary)

| When | What |
|------|------|
| Phase 1 | Scrapers for myG, Oxygen, Pittappillil, Nandilath G Mart |
| Phase 2 | Cleaning (2A), normalization with taxonomy v1.0 (2B), brand extraction with brands v1.1 (2C) |
| Phase 3 | PostgreSQL schema, loader, price history |
| Phase 4 | Read-only FastAPI with filters, summary, protection (timeout, caps, CORS, rate limit) |
| Phase 5 (phones) | Extraction report, matcher v1.1, Alembic + migration `0001`, match writer, `/products` and `/compare`; 32 cross-retailer products |
| 2026-10-29 | `data/` removed from git (history still contains it); tests moved to `quote_yard_test`; this plan replaced `Quote_Yard_Project_Master_Plan.md` |

# Quote Yard

Price comparison for Kerala retailers. Scrapers collect listings from four
shops, a pipeline cleans and classifies them, a matcher groups the same
product across shops, and an API serves the result to logged-in users.

```
scrapers -> data/ -> clean -> normalize -> brand -> PostgreSQL (loader)
         -> match (canonical products) -> alerts -> FastAPI -> React
```

| Retailer | Site | Scraper |
|----------|------|---------|
| myG | myg.in | `scrapers/myg_scraper.py` |
| Oxygen | oxygendigitalshop.com | `scrapers/oxygen_scraper.py` |
| Pittappillil | pittappillilonline.com | `scrapers/pittappillil_scraper.py` |
| Nandilath G Mart | nandilathgmart.com | `scrapers/nandilath_scraper.py` |

**Status (2026-10-29):** 2,965 listings loaded; mobile phones matched into
113 products, 32 of them sold by 2+ retailers and served by `/products` and
`/compare`; 163 tests pass. What is next:
[`docs/roadmap.md`](docs/roadmap.md).

## Docs

| File | Contents |
|------|----------|
| [`docs/roadmap.md`](docs/roadmap.md) | Where the project is, what comes next, open issues |
| [`docs/decisions.md`](docs/decisions.md) | How each pipeline stage works and why, with baseline numbers |
| [`docs/scrapers.md`](docs/scrapers.md) | Per-retailer scraper notes, selectors, quirks, commands |
| [`docs/accounts-and-vendors.md`](docs/accounts-and-vendors.md) | Design proposals for accounts / watchlist / deals and vendor offers |

## Setup

Arch Linux, Python 3.14, PostgreSQL (local socket, current OS user).

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium      # only the scrapers need it
createdb quote_yard
python -m db.create_tables       # new database: creates the schema, stamps the Alembic head, seeds retailers
```

Existing database after pulling new code: `alembic upgrade head`.
Check that models and database agree: `alembic check`.

The database URL comes from `QUOTE_YARD_DATABASE_URL`
(default `postgresql+psycopg:///quote_yard`).

## Run the pipeline

One command runs everything:

```
python -m pipeline                          # scrape all 4 retailers, then process, load, match
python -m pipeline --only myg oxygen        # scrape only these retailers
python -m pipeline --skip-scrape            # reprocess the data/ already on disk
python -m pipeline --skip-scrape --dry-run  # nothing saved or emailed
```

Each retailer is scraped in its own process (a crash or hang never stops
the others). `data/` is backed up first; a file that comes back empty or
unreadable is restored from the backup, and one that shrinks by more than
half is flagged. The processing stages stop at the first failure. Only one
run at a time. Logs and the backup go to `logs/<timestamp>/` (the newest 14
runs are kept). Exit code: 0 OK, 1 a retailer needs attention, 2 a stage
failed.

The same steps by hand, in order (each is deterministic and safe to
repeat; the loader and the match writer have `--dry-run`):

```
python scrapers/<retailer>_scraper.py          # writes data/<retailer>_*.json
python data_processing/run_cleaning.py         # -> cleaned_data/
python data_processing/run_normalization.py    # -> normalized_data/
python data_processing/run_branding.py         # -> branded_data/
python -m db.loader                            # -> listings, categories, price history
python -m db.match_writer                      # -> canonical products, listing links
python -m api.send_alerts                      # -> price alert emails
```

Read-only reports (written to `reports/`): `python data_processing/review_normalized.py`,
`python -m matching.extract_phones`, `python -m matching.phone_matcher`.

## Daily schedule

```
deploy/install-scheduler.sh            # install: runs the pipeline daily at 02:00
deploy/install-scheduler.sh --remove   # uninstall
systemctl --user list-timers quote-yard-pipeline.timer   # next and last run
journalctl --user -u quote-yard-pipeline -e              # summary of the latest runs
systemctl --user start quote-yard-pipeline               # run now
```

A run missed while the machine was off starts at the next boot or login.
User timers only run while you are logged in; on a server run
`loginctl enable-linger $USER` once. Per-stage logs are in `logs/`.

## Run the API

```
uvicorn api.main:app --reload
```

Docs at http://127.0.0.1:8000/api/v1/docs. Most routes need a login, and during development
email codes print in this terminal. Session cookies are `Secure` by default; on plain http other
than localhost set `QUOTE_YARD_COOKIE_SECURE=false`. All settings are listed in `.env.example`. Settings: `QUOTE_YARD_CORS_ORIGINS`
(default `http://localhost:5173`), `QUOTE_YARD_RATE_LIMIT` (requests per minute
per client, default 120, `0` = off).

## Deploy

The API serves the built frontend from `frontend/dist`, so one service is the whole site.

```
deploy/install-api.sh [--lan]            # on the server, once
deploy/deploy.sh user@192.168.1.14       # from the laptop, after git push
```

`deploy.sh` builds the site, updates the server's code and database, and restarts
the service. It refuses to run with unpushed commits or during the nightly update.

## Tests

```
python -m pytest -q
```

Tests run against a separate database, `quote_yard_test` (override with
`QUOTE_YARD_TEST_DATABASE_URL`). It is created if missing and rebuilt on every
run. The suite refuses to start if the test URL is the real database or its
name does not end in `_test`.

## Layout

```
scrapers/          Playwright scrapers, one per retailer
data/              raw scraper output (not in git; backup: quote-yard-raw-data.tar.gz)
data_processing/   cleaning, normalization (taxonomy/), brand extraction (brands.json)
db/                models, migrations (Alembic), loader, match writer
matching/          phone extraction report and matcher
api/               FastAPI app (read-only data routes, accounts)
frontend/          React + Vite prototype (not yet connected to the API)
tests/             pytest suite
cleaned_data/ normalized_data/ branded_data/ reports/   regenerable, not in git
```

Import style: `data_processing/` scripts run by path
(`python data_processing/run_cleaning.py`); `db`, `api` and `matching` are
packages, run with `python -m` from the repo root.

## Ground rules

- Every stage is deterministic and versioned (`taxonomy_version`, `brands_version`, `matching_version`); the same input gives the same output.
- Mappings, brand aliases and matching rules are explicit and reviewable. Nothing is guessed: unknown or ambiguous cases are reported (`unmapped`, `brand_status: review`, matcher review list).
- Later stages never modify earlier layers. Raw data is never edited.
- The loader never deletes listings; the match writer never deletes products.
- Data routes never write; only account code does, through its own connection. Public claims ("cheapest", "save X") must be provable from the data.
- No AI extraction, no Kafka / Celery / Redis / microservices until a real need appears.
- Debug one change at a time: change, test, then the next change.

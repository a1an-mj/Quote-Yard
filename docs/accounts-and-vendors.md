# Accounts, watchlist, deals, vendors

The accounts backend is built (Phase 7). Saved items, alerts and deals are next in the same phase; vendors are Phase 12, after the first release.

## Accounts (built)

**Access:** the platform requires login. Public: `/health`, `/retailers`, the auth routes, and later the deals endpoint, for a landing page with what the site does, the 4 retailers and today's deals. Everything else returns 401. No Google sign-in, WhatsApp or phone codes in the first release.

| Endpoint (`/api/v1/auth`) | What it does |
|---------------------------|--------------|
| `POST /register` | Email + password. Emails a code. Same reply whether or not the address has an account |
| `POST /resend-code` | Another sign-up code |
| `POST /verify-email` | The code confirms the address and logs in |
| `POST /login` | Sets the session cookie. Unverified accounts get `email_not_verified`, only after the right password |
| `POST /logout` | Ends this session on the server |
| `GET /me` | The logged-in user, or 401 |
| `POST /forgot-password`, `POST /reset-password` | Same code system; a new password ends every session |

| Rule | Detail |
|------|--------|
| Passwords | argon2id (`argon2-cffi`). 8 to 128 characters, no composition rules |
| Codes | 6 digits, hashed; 10 minutes, single use, a new code cancels the old; 5 wrong tries kill it; one per minute, 5 per hour per address and purpose |
| Sessions | Opaque random token, only its SHA-256 stored, in an httpOnly SameSite=Lax cookie (`Secure` unless `QUOTE_YARD_COOKIE_SECURE=false`). 14 days |
| CSRF | State-changing auth requests need the `X-Quote-Yard` header; CORS with credentials from configured origins only |
| Abuse | Same reply for unknown addresses, equal password-check time, mail sent after the response. Per client address: 20 auth requests a minute (`QUOTE_YARD_AUTH_RATE_LIMIT`), 10 logins per account per 15 minutes, 20 registrations a day; hidden honeypot field |
| Writes | Data routes keep the read-only connection. Only account code writes, through a separate one |
| Mail | `QUOTE_YARD_MAIL_BACKEND`: `console` prints codes (development), `smtp` sends. See `.env.example`. First setup: a dedicated Gmail with an App Password; about 500 mails a day; a domain and provider later only change settings |

Limiters are per process and reset on restart, like the main limiter.

## Saved items and alerts (next)

A saved list, and one alert type: email when the lowest current price drops below a chosen amount, checked after each daily pipeline run.

### Remaining tables (via an Alembic migration)

| Table | Columns |
|-------|---------|
| `saved_products` | `user_id`, `canonical_product_id`, `price_when_saved`, `created_at`; unique per user and item |
| `featured_deals` | `id`, `canonical_product_id`, `is_active`, `is_manual`, `verified_by`, `verified_at`, `created_at` |

`price_when_saved` lets a later "dropped since you saved it" view work
without a schema change.

### Deals must be provable

Proposed rule: a listing or product in the latest scrape, not out of stock, at its lowest price in the last 90 days **and** below an earlier recorded price, with a drop of at least 2% or Rs 500. Most prices never change, so "at its lowest" alone would match nearly everything (2,874 of 3,048 listings on 2026-10-31, against 136 that really dropped). Five are picked once a day, and the biggest gaps between stores are added. Say "Lowest in 90 days" only once 90 days of history exist; until then "Lowest since we began tracking", with the real drop.

| Rule | Detail |
|------|--------|
| Source | A canonical product at 2+ retailers; prices come live from the matched listings, never typed in. A manual deal records `verified_by` and `verified_at`. |
| Claims | Generated from the data: "12,999 at Oxygen, 13,499 at Nandilath: save 500". The saving is between the listed retailers, not against a list price (none is stored). |
| "Cheapest" | Only "cheapest of the N retailers listed", only when every tracked retailer stocking it is included. Never "cheapest in Kerala". Not where myG truncation could change the answer. |
| Auto-hide | Any matched listing out of stock, last seen over 3 days ago, or saving below a minimum |
| Later | With daily scrapes, real price drops also qualify |

## Vendors

Local shops register, get reviewed, and publish weekly offers that appear
**next to** scraped prices.

| Principle | Detail |
|-----------|--------|
| Separate storage | Offers in their own tables, never in `listings` |
| Matched and validated | Each offer links to a canonical product and is checked (price, dates, product) before it shows |
| Reviewed identity | Business details reviewed before any offer is published |
| Visible source | Every price is labelled: scraped listing, verified-vendor offer (unreviewed offers are not shown). API price objects gain a `source` field. |
| Validity | Start and end dates, automatic expiry, weekly by default |
| Separate accounts | Vendor accounts are not a flag on `users` |
| Audit | Offer changes and review decisions are recorded |
| Sensitive data | Collect only what review needs (e.g. GST number, to decide) and protect it |

Depends on: canonical products (done for phones), accounts with verified
email, an admin review tool.

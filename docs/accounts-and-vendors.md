# Accounts, watchlist, deals, vendors

The accounts, saved items, alerts and deals backends are built (Phase 7). Vendors are Phase 12, after the first release.

## Accounts (built)

**Access:** the platform requires login. Public: `/health`, `/retailers`, the auth routes, and later the deals endpoint, for a landing page with what the site does, the 4 retailers and today's deals. Everything else returns 401. No Google sign-in, WhatsApp or phone codes in the first release.

| Endpoint (`/api/v1/auth`) | What it does |
|---------------------------|--------------|
| `POST /register` | First name (required), last name (optional), email + password. Emails a code. Same reply whether or not the address has an account |
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

## Saved items and alerts (built)

| Endpoint (`/api/v1/me`, login required) | What it does |
|---|---|
| `GET /saved`, `PUT` / `DELETE /saved/{product_id}` | A saved list. Saving twice changes nothing; `price_when_saved` is kept for a later "dropped since you saved it" |
| `GET /alerts`, `PUT` / `DELETE /alerts/{product_id}` | One alert per product: email when its lowest current price goes below `target_price` |

`python -m api.send_alerts [--dry-run]` is the pipeline's last stage. Only current, buyable offers count. It mails once, again only for a lower price, and re-arms when the price climbs back to the target. Each alert commits after its email, so a failed mail is retried on the next run and a delivered one is never repeated.

## Deals (built)

`GET /api/v1/public/deals` is public and returns up to 5, with no store links. Everything is computed from recorded prices (`api/deals.py`), with no deals table.

- **Price drop:** current and buyable, at its lowest price of the last 90 days, at least Rs 500 below the price before it, changed in the last 7 days, and (for a matched product) no tracked store cheaper. Most prices never change, so "at its lowest" alone would match nearly everything (2,874 of 3,048 listings on 2026-10-31).
- **Store gap:** a matched product whose lowest store is at least Rs 500 below the next store.
- **Picking:** one deal per product, at most 2 gaps, different brands first, the same picks all day (seeded by the date in IST), and never padded when there are too few.
- **Wording:** "Lowest in 90 days" only when that listing has 90 days of history; until then "Lowest since we began tracking", with the real earlier price. Savings are between recorded prices or stores, never against an MRP.

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

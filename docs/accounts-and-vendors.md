# Accounts, watchlist, deals, vendors

The accounts, saved items, alerts and deals backends are built (Phase 7). The vendor system (Phase 12) is built too, but shops can only reach it once the site is public (Phase 10).

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

## Vendors (built)

Local shops are invited, get reviewed, and publish offers that appear **next to** store prices. Customers contact the shop directly; Quote Yard takes no orders or payments.

| Rule | Detail |
|------|--------|
| Joining | Invite only. An admin sends a one-time link to the shop's email, valid 7 days; a new invite cancels the old link. The link carries its token after the `#`, so it stays out of server logs |
| Accounts | Separate tables, login and cookie (`qy_vendor_session`) from customers. A shop login cannot read customer data, and the reverse |
| Review | A shop waits as `pending` until an admin approves it. Offers appear only while the shop is `approved`; suspending hides them all at once, reinstating restores them |
| Admins | Customer accounts listed in `QUOTE_YARD_ADMIN_EMAILS`. They use `/admin` |
| Offers | **Not reviewed one by one** (user's decision, 2026-11-01): they go live on their start date after the automatic checks. An admin can remove any offer |
| Automatic checks | Product has a current store price; price is 50% to 150% of the lowest store price (likely typing mistakes are refused); start date not past and at most 30 days ahead; at most 31 days long; one running offer per product; at most 200 per shop |
| Expiry | Offers stop showing after their end date (India time) with no background job |
| Separate from store data | Own tables, never in `listings`. Offers **do not** affect lowest prices, comparisons, price history, alerts or deals |
| Labelled | Store offers have `source: scraped_listing`, shop offers `source: verified_vendor`. The page says the shop sets the price itself |
| Shown to customers | Shop name, town, district, phone, offer dates, and a Google Maps link built by the server, so a shop cannot supply its own link. No free-text notes |
| Sensitive data | Optional GST number, seen only by admins. Shops cannot edit approved details themselves |
| Audit | `vendor_audit_log` records invites, review decisions and every offer change |

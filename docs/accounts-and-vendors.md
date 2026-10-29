# Accounts, watchlist, deals, vendors (design proposals)

Not built yet. Roadmap step 4 (accounts) and "later" (vendors).

## Accounts and watchlist

### Open decision: what needs a login

The original design gates the whole platform (search, listings, comparison)
behind login, with only a public deal teaser. **Recommended instead:**
browsing and comparison stay public; an account is needed for the
watchlist, alerts and anything personal. Reasons: a comparison site is found
through search engines and shared links, which a login wall blocks; free
sign-up barely slows scrapers, while the rate limiter already does. If
gating is kept, every catalog / listing / product route gains a
`require_user` dependency and the API tests switch to an authenticated
client.

### Decided

- Open sign-up with email and password; **email verification by OTP**.
- Token sessions and secure password hashing; protection against automated sign-up and login abuse.
- Vendor accounts are a separate system and a separate phase.

### Proposed details

| Topic | Proposal |
|-------|----------|
| Session token | Opaque random token (not JWT); only its SHA-256 stored. Delivered in an httpOnly, SameSite=Lax cookie (`Secure` in production). 14-day expiry; logout revokes. |
| CSRF | Required custom header on state-changing requests; CORS with credentials from configured origins only |
| Passwords | argon2id (`argon2-cffi`), or stdlib `hashlib.scrypt` if no wheel for Python 3.14. 10-128 chars, no composition rules, not equal to the email |
| OTP | 6 digits from `secrets`, stored hashed; 10 minutes, single use, a new code cancels the old; 5 wrong tries invalidate it; 60 s resend cooldown and per-email / per-IP hourly caps. Unverified accounts cannot log in. Same mechanism later for password reset. |
| Mail | Console backend in development, fake sender in tests, SMTP from environment in production. Needs a provider and a sending domain with SPF and DKIM, or codes land in spam. |
| Login abuse | Generic error, equal timing for unknown emails, short per-account backoff, stricter rate limit on `/auth/login` |
| Sign-up abuse | Stricter per-IP rate limit and a daily per-IP account cap on `/auth/register`, hidden honeypot field, optional CAPTCHA (e.g. Cloudflare Turnstile) |
| Writes | Product and listing routes stay read-only. Only auth, watchlist and deal-admin code writes, through a separate connection, to the new tables only. Two database roles in deployment. |

### Schema (new tables, via an Alembic migration)

| Table | Columns |
|-------|---------|
| `users` | `id`, `email` (casefolded, unique), `password_hash`, `is_active`, `email_verified_at`, `created_at`, `last_login_at` |
| `email_codes` | `id`, `user_id`, `code_hash`, `purpose`, `expires_at`, `attempts`, `used_at`, `created_at` |
| `sessions` | `id`, `user_id`, `token_hash` (unique), `created_at`, `expires_at`, `revoked_at` (model `UserSession`, to avoid clashing with SQLAlchemy `Session`) |
| `watchlist_items` | `user_id`, `canonical_product_id` or `listing_id`, `price_when_saved`, `created_at`; unique per user and item |
| `featured_deals` | `id`, `canonical_product_id`, `is_active`, `is_manual`, `verified_by`, `verified_at`, `created_at` |

`price_when_saved` lets a later "dropped since you saved it" view work
without a schema change.

### Endpoints (under `/api/v1`)

| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/auth/register`, `/auth/verify-email`, `/auth/resend-code`, `/auth/login` | Public, rate limited |
| POST | `/auth/logout` · GET `/auth/me` | Logged in |
| GET / PUT / DELETE | `/me/watchlist`, `/me/watchlist/{id}` (PUT is idempotent) | Logged in |
| GET | `/public/deals` | Public |

Admin commands: `python -m db.users` (list, deactivate, set password),
`python -m db.deals` (create manual, list, deactivate).

### Deals must be provable

| Rule | Detail |
|------|--------|
| Source | A canonical product at 2+ retailers; prices come live from the matched listings, never typed in. A manual deal records `verified_by` and `verified_at`. |
| Claims | Generated from the data: "12,999 at Oxygen, 13,499 at Nandilath: save 500". The saving is between the listed retailers, not against a list price (none is stored). |
| "Cheapest" | Only "cheapest of the N retailers listed", only when every tracked retailer stocking it is included. Never "cheapest in Kerala". Not where myG truncation could change the answer. |
| Auto-hide | Any matched listing out of stock, last seen over 3 days ago, or saving below a minimum |
| Later | With daily scrapes, real price drops also qualify |

### Rough plan (about six days)

1. Users, sessions, hashing, register / login / logout / me, cookie and CSRF, tests
2. OTP: codes, mail backends, verify / resend, send limits, tests
3. Abuse protection, per-user rate limit, `db.users`
4. Watchlist; deal generation and `/public/deals`
5-6. Frontend pages (landing, register / verify / login, dashboard, watchlist)

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

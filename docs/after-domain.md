# After buying the domain (quoteyard.in)

The domain is bought by Rohith, in his name, and added to a free Cloudflare
account (its nameservers set at the seller). Then, in this order:

## Must do

1. **Done 2026-11-14. Permanent link: a named Cloudflare tunnel** for
   `quoteyard.in` and `www.quoteyard.in` (`deploy/install-site-tunnel.sh`,
   service `quote-yard-tunnel`). The quick tunnel and its watchdog are removed;
   the status report opens `QUOTE_YARD_SITE_URL`.
   - Cloudflare: "Always Use HTTPS" is on, and a "Redirect from WWW to root"
     rule sends `www.quoteyard.in` to `quoteyard.in` (both done 2026-11-14).
2. **Done 2026-11-14. Server settings** (`.env` on the server):
   - `QUOTE_YARD_SITE_URL=https://quoteyard.in`, used in shop invite and reset links.
   - `QUOTE_YARD_ALLOWED_HOSTS=quoteyard.in,www.quoteyard.in,localhost,127.0.0.1`.
   - `QUOTE_YARD_COOKIE_SECURE=true`.
3. **Done 2026-11-15. Google sign-in** (client in Rohith's Google Cloud, app in production):
   - In Google Cloud (Rohith's account), add `https://quoteyard.in` under
     Authorised JavaScript origins.
   - Set `QUOTE_YARD_GOOGLE_CLIENT_ID` on the server.
   - Publish the OAuth consent screen: app name, logo, the Privacy and Terms
     links on quoteyard.in, and verify the domain. Until it is published, only
     listed test users can sign in.
4. **Skipped for now: contact email** such as `contact@quoteyard.in`, forwarded free with Cloudflare
   Email Routing. Put it on the Privacy and Terms pages.
5. **Done 2026-11-15. Privacy and Terms pages:** quoteyard.in, contact
   quoteyard.alerts@gmail.com, Cloudflare and Google sign-in listed, new date.
6. **Done 2026-11-14. Update the care guide** (https://claude.ai/artifact/PXqbtjJs6AD487DwGCc5zJ)
   and tell testers the new address.

## Could do

- **Sending email from the domain**, e.g. `alerts@quoteyard.in` instead of Gmail,
  with SPF, DKIM and DMARC records so mail does not land in spam.
- **Cloudflare settings:** Always use HTTPS, minimum TLS 1.2, Bot Fight Mode, and
  a rate-limit rule on `/api/v1/auth/*`.
- **A longer HSTS** (`includeSubDomains`, then preload) once everything is
  on https for good.
- **An outside uptime check** (e.g. a free monitor pinging
  `https://quoteyard.in/api/v1/health`), so someone hears when the server's
  internet is down. Today's emails come from the server itself, so they stop too.
- **Affiliate programmes** (Flipkart and others): they need a real site address.
- **Trademark check** for the name "Quote Yard".
- **Search engines:** Google Search Console, a sitemap and robots.txt.
- **Link previews:** a share image (og:image) and a favicon for WhatsApp and
  social links.
- **Store relations:** a "Stores: contact or opt out" line on the site, and a
  scraper user agent that names the site and contact address.

## Security to-dos not tied to the domain

- Upgrade `react-router` to version 7 (a published redirect bug in version 6).
- Disk encryption on the server, and off-site backups. This is Rohith's
  decision: it means reinstalling Ubuntu with encryption.

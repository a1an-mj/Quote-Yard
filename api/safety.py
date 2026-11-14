"""Which site addresses the server answers to, and the browser safety headers.

Allowed addresses: a request naming any other address (Host header) is refused,
so links the server builds from the address, like a shop's password reset
link, can never point at someone else's site.
"""

import os
from urllib.parse import urlsplit

DEFAULT_HOSTS = ("localhost", "127.0.0.1", "*.trycloudflare.com")

HEADERS = [
    # Never shown inside another site's frame (stops "clickjacking").
    (b"x-frame-options", b"DENY"),
    (b"content-security-policy", b"frame-ancestors 'none'"),
    # The browser must not guess a file's type and run it as a script.
    (b"x-content-type-options", b"nosniff"),
    # Other sites learn only that a visitor came from Quote Yard, not which page.
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), payment=()"),
]
HSTS = (b"strict-transport-security", b"max-age=31536000")


def allowed_hosts() -> list[str]:
    """QUOTE_YARD_ALLOWED_HOSTS (comma separated) replaces the defaults; the
    host of QUOTE_YARD_SITE_URL is always allowed."""
    raw = os.environ.get("QUOTE_YARD_ALLOWED_HOSTS", "").strip()
    hosts = [h.strip().lower() for h in raw.split(",") if h.strip()] if raw else list(DEFAULT_HOSTS)
    site = urlsplit(os.environ.get("QUOTE_YARD_SITE_URL", "")).hostname
    if site and site not in hosts:
        hosts.append(site)
    return hosts


class SafetyHeadersMiddleware:
    """Pure ASGI: adds the headers to every response, errors and site files too.
    HSTS ("always use https here") only on https requests."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        extra = HEADERS + ([HSTS] if scope.get("scheme") == "https" else [])

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                have = {name.lower() for name, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [
                    (name, value) for name, value in extra if name not in have]
            await send(message)

        await self.app(scope, receive, send_with_headers)

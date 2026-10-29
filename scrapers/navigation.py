"""Page navigation shared by the scrapers.

goto_with_retry() is page.goto() with one retry for a page that did not load
(a timeout or a network error such as net::ERR_CONNECTION_RESET). A page that
loads with an HTTP error (403, 404, 5xx) is returned as it is, never retried:
the scrapers stop the category on those, and a block must not be hammered.
If the retry fails too, the error is raised, so each scraper's own error
handling still applies.
"""

import logging
import time

from playwright.sync_api import Error as PlaywrightError

RETRY_DELAY_S = 5

log = logging.getLogger(__name__)


def _is_load_failure(exc: Exception) -> bool:
    # Playwright's TimeoutError subclasses its Error; network failures are
    # plain Errors whose message carries the net:: code.
    return type(exc).__name__ == "TimeoutError" or "net::" in str(exc)


def goto_with_retry(page, url: str, *, retries: int = 1, delay_s: float = RETRY_DELAY_S, **kwargs):
    """page.goto(url, **kwargs), retried `retries` times if the page did not load."""
    for attempt in range(retries + 1):
        try:
            return page.goto(url, **kwargs)
        except PlaywrightError as exc:
            if attempt == retries or not _is_load_failure(exc):
                raise
            log.warning("Page did not load (%s); retrying in %ss: %s",
                        str(exc).splitlines()[0], delay_s, url)
            time.sleep(delay_s)

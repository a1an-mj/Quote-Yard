import sys
from pathlib import Path

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scrapers"))

from navigation import goto_with_retry


class FakePage:
    """page.goto() raising the given errors in turn, then returning `response`."""

    def __init__(self, *errors, response="response"):
        self.errors = list(errors)
        self.response = response
        self.calls = []

    def goto(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.errors:
            raise self.errors.pop(0)
        return self.response


def test_loads_first_time():
    page = FakePage()
    assert goto_with_retry(page, "u", wait_until="domcontentloaded", timeout=5) == "response"
    assert page.calls == [("u", {"wait_until": "domcontentloaded", "timeout": 5})]


def test_timeout_retried_once():
    page = FakePage(PlaywrightTimeoutError("Timeout 30000ms exceeded."))
    assert goto_with_retry(page, "u", delay_s=0) == "response"
    assert len(page.calls) == 2


def test_network_error_retried():
    page = FakePage(PlaywrightError("net::ERR_CONNECTION_RESET at https://x"))
    assert goto_with_retry(page, "u", delay_s=0) == "response"


def test_second_failure_raised_to_the_scraper():
    page = FakePage(PlaywrightTimeoutError("t1"), PlaywrightTimeoutError("t2"))
    with pytest.raises(PlaywrightTimeoutError, match="t2"):
        goto_with_retry(page, "u", delay_s=0)
    assert len(page.calls) == 2


def test_other_errors_not_retried():
    page = FakePage(PlaywrightError("Target page, context or browser has been closed"))
    with pytest.raises(PlaywrightError):
        goto_with_retry(page, "u", delay_s=0)
    assert len(page.calls) == 1


def test_http_error_response_returned_not_retried():
    # A 403 / 404 / 5xx is a loaded page: returned once, the scraper decides.
    page = FakePage(response="403 response")
    assert goto_with_retry(page, "u", delay_s=0) == "403 response"
    assert len(page.calls) == 1

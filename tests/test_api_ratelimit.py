import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.main import API_PREFIX, create_app, rate_limit_per_minute
from api.ratelimit import RateLimiter

URL = f"{API_PREFIX}/openapi.json"


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


# ---- the limiter itself -----------------------------------------------------

def test_allows_up_to_the_limit_then_blocks():
    limiter = RateLimiter(limit=3, window=60, clock=FakeClock())
    assert [limiter.check("a") for _ in range(3)] == [None, None, None]
    assert limiter.check("a") == pytest.approx(60.0)


def test_window_slides():
    clock = FakeClock()
    limiter = RateLimiter(limit=2, window=60, clock=clock)
    assert limiter.check("a") is None
    clock.advance(30)
    assert limiter.check("a") is None
    assert limiter.check("a") == pytest.approx(30.0)
    clock.advance(31)
    assert limiter.check("a") is None


def test_clients_are_counted_separately():
    limiter = RateLimiter(limit=1, clock=FakeClock())
    assert limiter.check("a") is None
    assert limiter.check("b") is None
    assert limiter.check("a") is not None


def test_oldest_client_is_evicted_when_full():
    limiter = RateLimiter(limit=5, max_clients=2, clock=FakeClock())
    for key in ("a", "b", "c"):
        limiter.check(key)
    assert set(limiter.hits) == {"b", "c"}


def test_expired_clients_are_purged_before_evicting():
    clock = FakeClock()
    limiter = RateLimiter(limit=5, window=60, max_clients=2, clock=clock)
    limiter.check("a")
    limiter.check("b")
    clock.advance(100)
    limiter.check("c")
    assert set(limiter.hits) == {"c"}


# ---- through the app --------------------------------------------------------

def test_requests_over_the_limit_get_429():
    client = TestClient(create_app(rate_limit=2))
    assert [client.get(URL).status_code for _ in range(3)] == [200, 200, 429]
    response = client.get(URL)
    assert response.status_code == 429
    assert response.json() == {"detail": "rate limit exceeded"}
    assert int(response.headers["retry-after"]) >= 1


def test_health_is_never_limited():
    client = TestClient(create_app(rate_limit=1))
    codes = [client.get(f"{API_PREFIX}/health").status_code for _ in range(5)]
    assert 429 not in codes


def test_429_still_carries_cors_headers():
    client = TestClient(create_app(rate_limit=1))
    headers = {"Origin": "http://localhost:5173"}
    client.get(URL, headers=headers)
    response = client.get(URL, headers=headers)
    assert response.status_code == 429
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_each_client_address_has_its_own_budget():
    app = create_app(rate_limit=1)
    one = TestClient(app, client=("10.0.0.1", 1111))
    two = TestClient(app, client=("10.0.0.2", 2222))
    assert one.get(URL).status_code == 200
    assert one.get(URL).status_code == 429
    assert two.get(URL).status_code == 200


def test_zero_disables_the_limit():
    client = TestClient(create_app(rate_limit=0))
    assert all(client.get(URL).status_code == 200 for _ in range(10))


# ---- configuration ----------------------------------------------------------

def test_env_default_and_valid_value(monkeypatch):
    monkeypatch.delenv("QUOTE_YARD_RATE_LIMIT", raising=False)
    assert rate_limit_per_minute() == 120
    monkeypatch.setenv("QUOTE_YARD_RATE_LIMIT", "30")
    assert rate_limit_per_minute() == 30


@pytest.mark.parametrize("bad", ["abc", "-5", "1.5"])
def test_env_rejects_bad_values(monkeypatch, bad):
    monkeypatch.setenv("QUOTE_YARD_RATE_LIMIT", bad)
    with pytest.raises(RuntimeError):
        rate_limit_per_minute()

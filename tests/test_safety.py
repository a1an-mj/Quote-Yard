import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app, create_app
from api.safety import DEFAULT_HOSTS, allowed_hosts

client = TestClient(app)


def test_every_response_has_the_safety_headers():
    for path in ("/api/v1/health", "/api/v1/no-such-thing"):
        r = client.get(path)
        assert r.headers["x-frame-options"] == "DENY"
        assert r.headers["content-security-policy"] == "frame-ancestors 'none'"
        assert r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_hsts_only_over_https():
    assert "strict-transport-security" not in client.get("/api/v1/health").headers
    https = TestClient(app, base_url="https://testserver")
    assert https.get("/api/v1/health").headers["strict-transport-security"] == "max-age=31536000"


def test_a_fake_site_address_is_refused():
    r = client.get("/api/v1/health", headers={"Host": "evil.example"})
    assert r.status_code == 400


def test_the_tunnel_and_local_addresses_are_allowed():
    for host in ("abc-def.trycloudflare.com", "localhost:8000", "127.0.0.1"):
        assert client.get("/api/v1/health", headers={"Host": host}).status_code == 200


def test_default_hosts_and_the_site_url(monkeypatch):
    monkeypatch.delenv("QUOTE_YARD_ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("QUOTE_YARD_SITE_URL", "https://quoteyard.in")
    assert allowed_hosts() == [*DEFAULT_HOSTS, "quoteyard.in"]
    built = TestClient(create_app(rate_limit=0))
    assert built.get("/api/v1/health", headers={"Host": "quoteyard.in"}).status_code == 200
    assert built.get("/api/v1/health", headers={"Host": "evil.example"}).status_code == 400

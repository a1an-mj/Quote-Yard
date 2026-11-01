import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.main import create_app


@pytest.fixture
def site(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>app</html>")
    (tmp_path / "assets" / "app-abc.js").write_text("js")
    (tmp_path.parent / "secret.txt").write_text("secret")
    monkeypatch.setenv("QUOTE_YARD_SITE_DIR", str(tmp_path))
    return TestClient(create_app(rate_limit=2))


def test_home_and_app_routes_get_the_page(site):
    for path in ("/", "/search?q=x", "/product/5", "/login"):
        r = site.get(path)
        assert r.status_code == 200 and "app" in r.text
        assert r.headers["cache-control"] == "no-cache"


def test_assets_served_and_cached(site):
    r = site.get("/assets/app-abc.js")
    assert r.text == "js" and "immutable" in r.headers["cache-control"]


def test_missing_asset_is_a_404_not_the_page(site):
    assert site.get("/assets/gone.js").status_code == 404


def test_wrong_api_path_is_an_api_404(site):
    r = site.get("/api/v1/nope")
    assert r.status_code == 404 and r.json() == {"detail": "Not Found"}


def test_api_routes_still_win(site):
    assert site.get("/api/v1/products").status_code == 401


@pytest.mark.parametrize("path", ["/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"])
def test_no_files_outside_the_site_folder(site, path):
    assert "secret" not in site.get(path).text


def test_site_files_do_not_use_the_api_rate_limit(site):
    for _ in range(5):
        assert site.get("/").status_code == 200
    codes = [site.get("/api/v1/products").status_code for _ in range(3)]
    assert codes[-1] == 429


def test_no_site_without_a_build(tmp_path, monkeypatch):
    monkeypatch.setenv("QUOTE_YARD_SITE_DIR", str(tmp_path))
    assert TestClient(create_app(rate_limit=0)).get("/").status_code == 404

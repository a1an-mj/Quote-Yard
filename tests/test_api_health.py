import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.deps import get_api_engine, get_session
from api.main import app


@pytest.fixture(scope="module")
def db_up():
    try:
        with get_api_engine().connect():
            pass
    except OperationalError:
        pytest.skip("PostgreSQL not reachable")


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_ok(db_up, client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["database"] == "ok"
    assert isinstance(body["listings"], int)


def test_health_503_when_database_is_down(client):
    class Broken:
        def scalar(self, *args, **kwargs):
            raise OperationalError("select", {}, Exception("down"))

    app.dependency_overrides[get_session] = lambda: Broken()
    assert client.get("/api/v1/health").status_code == 503


def test_docs_live_under_the_prefix(client):
    assert client.get("/api/v1/docs").status_code == 200
    assert client.get("/api/v1/openapi.json").status_code == 200


def test_cors_allows_the_vite_origin_for_get(client):
    r = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_api_connection_is_read_only(db_up):
    with Session(get_api_engine()) as s:
        with pytest.raises(DBAPIError):
            s.execute(text("INSERT INTO retailers (name) VALUES ('should-fail')"))


def test_api_connection_has_a_statement_timeout(db_up):
    with Session(get_api_engine()) as s:
        assert s.scalar(text("SHOW statement_timeout")) in ("5s", "5000ms")
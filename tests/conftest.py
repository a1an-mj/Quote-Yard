import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

# Tests never touch the real database. Every test, and everything it imports
# (db.session, api.deps), reads QUOTE_YARD_DATABASE_URL, so point it at a
# separate database before any of that runs.
TEST_URL = os.environ.get(
    "QUOTE_YARD_TEST_DATABASE_URL", "postgresql+psycopg:///quote_yard_test"
)
_real_url = os.environ.get("QUOTE_YARD_DATABASE_URL", "postgresql+psycopg:///quote_yard")
_test_db = make_url(TEST_URL).database or ""
if TEST_URL == _real_url or not _test_db.endswith("_test"):
    raise RuntimeError(
        f"Refusing to run tests against {TEST_URL!r}: the test database must be "
        "separate from the real one and its name must end in '_test'."
    )
os.environ["QUOTE_YARD_DATABASE_URL"] = TEST_URL

# The API tests share one app instance; keep the rate limiter out of their way.
# tests/test_api_ratelimit.py builds its own apps with explicit limits.
os.environ["QUOTE_YARD_RATE_LIMIT"] = "0"


def _ensure_database() -> None:
    """Create the test database if it does not exist yet."""
    admin = create_engine(
        make_url(TEST_URL).set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin.connect() as conn:
        found = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": _test_db}
        ).first()
        if not found:
            conn.execute(text(f'CREATE DATABASE "{_test_db}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """Rebuild the test schema from the models once per run (fresh every time)."""
    from db.models import Base

    try:
        _ensure_database()
    except OperationalError:
        yield  # PostgreSQL down: the database tests skip themselves
        return
    engine = create_engine(TEST_URL)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(engine)
    engine.dispose()
    yield

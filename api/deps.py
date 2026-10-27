"""API database access: read-only connection with a query timeout."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from db.session import get_database_url

STATEMENT_TIMEOUT_MS = 5000


@lru_cache
def get_api_engine() -> Engine:
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        connect_args={
            "options": (
                "-c default_transaction_read_only=on "
                f"-c statement_timeout={STATEMENT_TIMEOUT_MS}"
            )
        },
    )


def get_session() -> Iterator[Session]:
    with Session(get_api_engine()) as session:
        yield session
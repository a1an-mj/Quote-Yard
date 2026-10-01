"""Quote Yard - database connection."""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# Unix-socket connection as the current OS user (works with a default Arch setup).
DEFAULT_URL = "postgresql+psycopg:///quote_yard"


def get_database_url() -> str:
    return os.environ.get("QUOTE_YARD_DATABASE_URL", DEFAULT_URL)


def get_engine(echo: bool = False) -> Engine:
    return create_engine(get_database_url(), echo=echo)
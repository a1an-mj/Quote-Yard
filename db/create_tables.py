"""
Create all tables and seed the four retailers. Safe to run repeatedly.
Fills in base_url where it is empty; never overwrites an existing value.

On a new database create_all builds the latest schema, so it is stamped as
the Alembic head. An existing database is upgraded with Alembic instead:
    alembic upgrade head

Usage (from the repo root):  python -m db.create_tables
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from db.models import Base, Retailer
from db.session import get_engine

# Origin only: scheme + host, no trailing slash.
RETAILERS = {
    "myG": "https://www.myg.in",
    "Oxygen": "https://www.oxygendigitalshop.com",              # fill from the query output
    "Pittappillil": "https://www.pittappillilonline.com",
    "Nandilath G Mart": "https://nandilathgmart.com",    # fill from the query output
}


ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def main() -> None:
    engine = get_engine()
    is_new = not inspect(engine).has_table("listings")
    Base.metadata.create_all(engine)
    if is_new:
        command.stamp(Config(str(ALEMBIC_INI)), "head")
        print("New database: schema created and stamped at the Alembic head.")

    with Session(engine) as session:
        existing = {r.name: r for r in session.scalars(select(Retailer))}
        for name, base_url in RETAILERS.items():
            retailer = existing.get(name)
            if retailer is None:
                session.add(Retailer(name=name, base_url=base_url))
            elif retailer.base_url is None:
                retailer.base_url = base_url
        session.commit()

        print("Retailers:")
        for r in session.scalars(select(Retailer).order_by(Retailer.id)):
            print(f"  {r.id}  {r.name:<18} {r.base_url}")
    print("Tables ready.")


if __name__ == "__main__":
    main()
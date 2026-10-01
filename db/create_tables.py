"""
Create all tables and seed the four retailers. Safe to run repeatedly.

Usage (from the repo root):  python -m db.create_tables
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Base, Retailer
from db.session import get_engine

RETAILERS = ["myG", "Oxygen", "Pittappillil", "Nandilath G Mart"]


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        existing = set(session.scalars(select(Retailer.name)))
        for name in RETAILERS:
            if name not in existing:
                session.add(Retailer(name=name))
        session.commit()

        print("Retailers:")
        for r in session.scalars(select(Retailer).order_by(Retailer.id)):
            print(f"  {r.id}  {r.name}")
    print("Tables ready.")


if __name__ == "__main__":
    main()
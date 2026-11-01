"""Email users whose price alerts have been reached. Last stage of the pipeline.

Usage (from the repo root):
    python -m api.send_alerts --dry-run    # report, send nothing
    python -m api.send_alerts

Each alert commits after its own email, so a failure never resends the mail
already delivered, and the next run retries the rest. Exit code 1 if any failed.
"""

import argparse
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.freshness import is_current
from api.mailer import get_mailer
from db.models import CanonicalProduct, Listing, PriceAlert, Retailer, User
from db.session import get_engine


def lowest_offer(session: Session, product_id: int):
    """(price, store, url) of the cheapest current, buyable listing, or None."""
    return session.execute(
        select(Listing.current_price, Retailer.name, Listing.url)
        .join(Retailer, Retailer.id == Listing.retailer_id)
        .where(Listing.canonical_product_id == product_id, is_current,
               Listing.availability != "Out of stock")
        .order_by(Listing.current_price, Listing.id)
        .limit(1)
    ).first()


def send_alerts(session: Session, mailer, dry_run: bool = False) -> dict:
    stats = {"checked": 0, "sent": 0, "failed": 0}
    rows = session.execute(
        select(PriceAlert, User.email, CanonicalProduct.name)
        .join(User, User.id == PriceAlert.user_id)
        .join(CanonicalProduct, CanonicalProduct.id == PriceAlert.canonical_product_id)
        .where(User.is_active.is_(True), User.email_verified_at.is_not(None))
        .order_by(PriceAlert.id)
    ).all()
    for alert, email, name in rows:
        stats["checked"] += 1
        offer = lowest_offer(session, alert.canonical_product_id)
        if offer is None:  # no current offer says nothing about the price
            continue
        price, store, url = offer
        if price >= alert.target_price:
            if alert.last_notified_price is not None and not dry_run:
                alert.last_notified_price = None  # back up: the next drop mails again
                session.commit()
            continue
        if alert.last_notified_price is not None and price >= alert.last_notified_price:
            continue
        if dry_run:
            stats["sent"] += 1
            continue
        body = (f"{name} is now Rs {price:,} at {store}, below your alert of "
                f"Rs {alert.target_price:,}.\n\n{url}\n\n"
                "Prices change often; check the store's page before you buy.\n")
        try:
            mailer.send(email, f"Price alert: {name}", body)
        except Exception as exc:
            stats["failed"] += 1
            print(f"Could not email alert {alert.id}: {exc}", file=sys.stderr)
            continue
        print(f"Sent alert {alert.id}")
        alert.last_notified_price = price
        alert.last_notified_at = datetime.now(timezone.utc)
        session.commit()
        stats["sent"] += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="report, send nothing")
    args = parser.parse_args()
    with Session(get_engine()) as session:
        stats = send_alerts(session, get_mailer(), args.dry_run)
    print(("DRY RUN " if args.dry_run else "") + f"alerts: {stats}")
    sys.exit(1 if stats["failed"] else 0)


if __name__ == "__main__":
    main()

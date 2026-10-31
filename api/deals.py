"""Today's deals for the public landing page. Everything comes from recorded prices.

A price drop: a current, buyable listing at its lowest price of the last 90
days, at least MIN_SAVING below the price it had before, changed in the last
RECENT_DAYS, and (for a matched product) no store listing it for less.
A store gap: a matched product whose lowest store is at least MIN_SAVING below
the next store. A price that never moved is not a deal, however low.
"""

import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.freshness import is_current
from db.models import CanonicalProduct, Listing, PriceHistory, Retailer

MIN_SAVING = 500
HISTORY_DAYS = 90
RECENT_DAYS = 7
DEALS_PER_DAY = 5
MAX_STORE_GAPS = 2
LOCAL_TIME = ZoneInfo("Asia/Kolkata")
OUT_OF_STOCK = "Out of stock"


@dataclass
class Deal:
    kind: str  # price_drop | store_gap
    key: str  # one deal per product or unmatched listing
    name: str
    brand: str | None
    retailer: str
    price: int
    compared_price: int  # the earlier price, or the next store's
    compared_retailer: str | None
    saving: int
    label: str
    checked_at: datetime


def find_deals(session: Session, now: datetime | None = None) -> list[Deal]:
    now = now or datetime.now(timezone.utc)
    rows = session.execute(
        select(Listing, Retailer.name, CanonicalProduct.name)
        .join(Retailer, Retailer.id == Listing.retailer_id)
        .outerjoin(CanonicalProduct, CanonicalProduct.id == Listing.canonical_product_id)
        .where(is_current, Listing.availability != OUT_OF_STOCK)
    ).all()
    if not rows:
        return []
    ids = [listing.id for listing, _, _ in rows]

    history = defaultdict(list)
    for listing_id, price, recorded_at in session.execute(
        select(PriceHistory.listing_id, PriceHistory.price, PriceHistory.recorded_at)
        .where(PriceHistory.listing_id.in_(ids),
               PriceHistory.recorded_at >= now - timedelta(days=HISTORY_DAYS))
        .order_by(PriceHistory.listing_id, PriceHistory.recorded_at, PriceHistory.id)
    ):
        history[listing_id].append((price, recorded_at))
    first_seen = dict(session.execute(
        select(PriceHistory.listing_id, func.min(PriceHistory.recorded_at))
        .where(PriceHistory.listing_id.in_(ids))
        .group_by(PriceHistory.listing_id)
    ).all())

    by_product = defaultdict(list)
    for listing, shop, _ in rows:
        if listing.canonical_product_id is not None:
            by_product[listing.canonical_product_id].append((listing.current_price, shop))
    lowest = {pid: min(offers)[0] for pid, offers in by_product.items()}

    best: dict[str, Deal] = {}

    def keep(deal: Deal) -> None:
        if deal.key not in best or deal.saving > best[deal.key].saving:
            best[deal.key] = deal

    for listing, shop, product_name in rows:
        pid = listing.canonical_product_id
        points = history.get(listing.id, [])
        price = listing.current_price
        if not points or price > min(p for p, _ in points):
            continue
        if pid is not None and price > lowest[pid]:
            continue
        # Walk back to the last different price; the point after it is when it changed.
        previous, changed_at = None, None
        for value, recorded_at in reversed(points):
            if value != price:
                previous = value
                break
            changed_at = recorded_at
        if previous is None or changed_at is None or previous - price < MIN_SAVING:
            continue
        if changed_at < now - timedelta(days=RECENT_DAYS):
            continue
        tracked = now - first_seen[listing.id] >= timedelta(days=HISTORY_DAYS)
        keep(Deal(
            kind="price_drop", key=f"p{pid}" if pid else f"l{listing.id}",
            name=product_name or listing.name, brand=listing.brand, retailer=shop,
            price=price, compared_price=previous, compared_retailer=None,
            saving=previous - price,
            label="Lowest in 90 days" if tracked else "Lowest since we began tracking",
            checked_at=listing.last_seen_at,
        ))

    names = {l.canonical_product_id: (n, l.brand, l.last_seen_at)
             for l, _, n in rows if l.canonical_product_id is not None}
    gaps = {}
    for pid, offers in by_product.items():
        per_store = {}
        for price, shop in offers:
            per_store[shop] = min(price, per_store.get(shop, price))
        if len(per_store) < 2:
            continue
        ranked = sorted((p, s) for s, p in per_store.items())
        (low, low_shop), (next_price, next_shop) = ranked[0], ranked[1]
        if next_price - low < MIN_SAVING:
            continue
        name, brand, seen = names[pid]
        gaps[pid] = Deal(
            kind="store_gap", key=f"p{pid}", name=name, brand=brand, retailer=low_shop,
            price=low, compared_price=next_price, compared_retailer=next_shop,
            saving=next_price - low, label="Lowest of the stores we track", checked_at=seen,
        )
    return sorted(best.values(), key=lambda d: d.key) + sorted(
        (g for g in gaps.values() if g.key not in best), key=lambda d: d.key
    )


def pick_deals(deals: list[Deal], day: date, count: int = DEALS_PER_DAY) -> list[Deal]:
    """The same picks all day. Different brands first; never padded with non-deals."""
    shuffled = sorted(deals, key=lambda d: d.key)
    random.Random(day.isoformat()).shuffle(shuffled)
    gaps = [d for d in shuffled if d.kind == "store_gap"][:MAX_STORE_GAPS]
    ordered = gaps + [d for d in shuffled if d.kind == "price_drop"]
    picked, brands = [], set()
    for deal in ordered:
        if len(picked) < count and deal.brand not in brands:
            picked.append(deal)
            brands.add(deal.brand)
    for deal in ordered:
        if len(picked) < count and deal not in picked:
            picked.append(deal)
    return picked


def todays_deals(session: Session, now: datetime | None = None) -> list[Deal]:
    now = now or datetime.now(timezone.utc)
    return pick_deals(find_deals(session, now), now.astimezone(LOCAL_TIME).date())

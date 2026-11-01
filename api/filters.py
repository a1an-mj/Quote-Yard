"""Shared listing filters, used by /listings and (next) /listings/summary."""

from datetime import datetime
from typing import Literal

from fastapi import HTTPException, Query
from sqlalchemy import func, select

from api.freshness import is_current
from db.models import Listing, ListingCategory, Retailer

MAX_QUERY_WORDS = 8


def escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input is matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ListingFilters:
    def __init__(
        self,
        q: str | None = Query(None, max_length=100, description="Every word must appear in the name"),
        retailer: str | None = Query(None, max_length=50),
        category: str | None = Query(None, max_length=100),
        product_type: str | None = Query(None, max_length=100),
        brand: str | None = Query(None, max_length=100),
        min_price: int | None = Query(None, ge=0),
        max_price: int | None = Query(None, ge=0),
        availability: Literal["In stock", "Out of stock", "Unknown"] | None = None,
        seen_since: datetime | None = None,
        current: bool = Query(False, description="Only listings from each retailer's latest, recent scrape"),
    ) -> None:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise HTTPException(status_code=422, detail="min_price cannot exceed max_price")
        self.q = (q or "").strip()
        self.retailer = retailer
        self.category = category
        self.product_type = product_type
        self.brand = brand
        self.min_price = min_price
        self.max_price = max_price
        self.availability = availability
        self.seen_since = seen_since
        self.current = current


def base_query(*columns):
    """SELECT ... FROM listings JOIN retailers; filters are applied on top."""
    return (
        select(*columns)
        .select_from(Listing)
        .join(Retailer, Retailer.id == Listing.retailer_id)
    )


def apply_filters(stmt, f: ListingFilters):
    for word in f.q.split()[:MAX_QUERY_WORDS]:
        stmt = stmt.where(Listing.name.ilike(f"%{escape_like(word)}%", escape="\\"))
    if f.retailer:
        stmt = stmt.where(func.lower(Retailer.name) == f.retailer.lower())
    if f.brand:
        stmt = stmt.where(func.lower(Listing.brand) == f.brand.lower())
    if f.min_price is not None:
        stmt = stmt.where(Listing.current_price >= f.min_price)
    if f.max_price is not None:
        stmt = stmt.where(Listing.current_price <= f.max_price)
    if f.availability:
        stmt = stmt.where(Listing.availability == f.availability)
    if f.seen_since:
        stmt = stmt.where(Listing.last_seen_at >= f.seen_since)
    if f.current:
        stmt = stmt.where(is_current)

    # EXISTS, not JOIN: a listing with two category rows must appear once.
    # Category and type must match on the SAME category row.
    if f.category or f.product_type:
        conditions = [ListingCategory.listing_id == Listing.id]
        if f.category:
            conditions.append(func.lower(ListingCategory.category) == f.category.lower())
        if f.product_type:
            conditions.append(func.lower(ListingCategory.product_type) == f.product_type.lower())
        stmt = stmt.where(select(ListingCategory.id).where(*conditions).exists())
    return stmt

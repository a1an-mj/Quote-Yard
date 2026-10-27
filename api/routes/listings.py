from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.orm import Session, selectinload

from api.deps import get_session
from api.filters import ListingFilters, apply_filters, base_query
from api.schemas import (
    CategoryOut,
    CheapestOut,
    ListingDetail,
    ListingOut,
    ListingPage,
    ListingSummary,
    PriceHistoryOut,
    PricePoint,
    RetailerRef,
    RetailerSummary,
)
from db.models import Listing, PriceHistory, Retailer

router = APIRouter(tags=["listings"])

# Every sort ends with id, so pages never shuffle between requests.
SORTS = {
    "name": (func.lower(Listing.name).asc(), Listing.id.asc()),
    "price_asc": (Listing.current_price.asc(), Listing.id.asc()),
    "price_desc": (Listing.current_price.desc(), Listing.id.asc()),
}

# Ids are 32-bit integers in the database; reject anything outside that range.
ListingId = Annotated[int, Path(ge=1, le=2_147_483_647)]


def to_out(listing: Listing, retailer: Retailer) -> ListingOut:
    return ListingOut(
        id=listing.id,
        name=listing.name,
        url=listing.url,
        retailer=RetailerRef(id=retailer.id, name=retailer.name),
        brand=listing.brand,
        brand_status=listing.brand_status,
        brand_candidates=listing.brand_candidates,
        price=listing.current_price,
        availability=listing.availability,
        last_seen_at=listing.last_seen_at,
        categories=[
            CategoryOut(
                category=c.category,
                product_type=c.product_type,
                mapping_status=c.mapping_status,
                raw_category=c.raw_category,
                raw_subcategory=c.raw_subcategory,
            )
            for c in sorted(listing.categories, key=lambda c: c.id)
        ],
    )


@router.get("/listings", response_model=ListingPage)
def search_listings(
    filters: ListingFilters = Depends(),
    sort: Literal["name", "price_asc", "price_desc"] = "name",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    total = session.scalar(apply_filters(base_query(func.count(Listing.id)), filters))
    stmt = (
        apply_filters(base_query(Listing, Retailer), filters)
        .order_by(*SORTS[sort])
        .limit(limit)
        .offset(offset)
        .options(selectinload(Listing.categories))
    )
    rows = session.execute(stmt).all()
    return ListingPage(
        total=total or 0,
        limit=limit,
        offset=offset,
        items=[to_out(listing, retailer) for listing, retailer in rows],
    )


# This route must stay above /listings/{listing_id}, or "summary" is read as an id.
@router.get("/listings/summary", response_model=ListingSummary)
def listings_summary(
    filters: ListingFilters = Depends(),
    session: Session = Depends(get_session),
):
    """Per-retailer count, min/max price and cheapest listing for the same filters.

    A rough comparison: it does not claim the listings are the same product.
    """
    stats = {
        retailer_id: (count, low, high)
        for retailer_id, count, low, high in session.execute(
            apply_filters(
                base_query(
                    Listing.retailer_id,
                    func.count(Listing.id),
                    func.min(Listing.current_price),
                    func.max(Listing.current_price),
                ),
                filters,
            ).group_by(Listing.retailer_id)
        )
    }
    cheapest = {
        listing.retailer_id: listing
        for listing in session.scalars(
            apply_filters(base_query(Listing), filters)
            .ext(distinct_on(Listing.retailer_id))
            .order_by(Listing.retailer_id, Listing.current_price, Listing.id)
        )
    }
    retailers = session.execute(
        select(Retailer.id, Retailer.name).order_by(Retailer.id)
    ).all()

    rows = []
    for retailer_id, name in retailers:
        count, low, high = stats.get(retailer_id, (0, None, None))
        best = cheapest.get(retailer_id)
        rows.append(
            RetailerSummary(
                retailer=name,
                listings=count,
                min_price=low,
                max_price=high,
                cheapest=CheapestOut(
                    id=best.id, name=best.name, url=best.url, price=best.current_price
                )
                if best
                else None,
            )
        )
    return ListingSummary(total=sum(r.listings for r in rows), retailers=rows)


@router.get("/listings/{listing_id}", response_model=ListingDetail)
def get_listing(listing_id: ListingId, session: Session = Depends(get_session)):
    row = session.execute(
        base_query(Listing, Retailer)
        .where(Listing.id == listing_id)
        .options(selectinload(Listing.categories))
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="listing not found")
    listing, retailer = row
    return ListingDetail(
        **to_out(listing, retailer).model_dump(),
        first_seen_at=listing.first_seen_at,
        taxonomy_version=listing.taxonomy_version,
        brands_version=listing.brands_version,
    )


@router.get("/listings/{listing_id}/prices", response_model=PriceHistoryOut)
def listing_prices(listing_id: ListingId, session: Session = Depends(get_session)):
    """Price history, oldest first. Has a single point until the loader has run again."""
    if session.scalar(select(Listing.id).where(Listing.id == listing_id)) is None:
        raise HTTPException(status_code=404, detail="listing not found")
    rows = session.execute(
        select(PriceHistory.price, PriceHistory.availability, PriceHistory.recorded_at)
        .where(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.recorded_at.asc(), PriceHistory.id.asc())
    ).all()
    return PriceHistoryOut(
        listing_id=listing_id,
        points=[
            PricePoint(price=price, availability=availability, recorded_at=recorded_at)
            for price, availability, recorded_at in rows
        ],
    )

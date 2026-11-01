from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from api.deps import get_session
from api.filters import MAX_QUERY_WORDS, escape_like
from api.freshness import is_current
from api.schemas import (
    CompareOut,
    ListingPrices,
    OfferOut,
    PricePoint,
    ProductDetail,
    ProductOut,
    ProductPage,
    ProductPriceHistory,
    ProductSpecs,
    RetailerOffer,
    RetailerRef,
)
from db.models import CanonicalProduct, Listing, PriceHistory, Retailer

router = APIRouter(tags=["products"])

ProductId = Annotated[int, Path(ge=1, le=2_147_483_647)]
OUT_OF_STOCK = "Out of stock"

# Prices of listings that can be bought; an out-of-stock listing never sets
# a product's price range or wins a comparison. Counts, prices and the
# product list use current listings only (api/freshness.py).
_buyable_price = case(
    (Listing.availability != OUT_OF_STOCK, Listing.current_price), else_=None
)
_stats = (
    select(
        Listing.canonical_product_id.label("product_id"),
        func.count(Listing.id).label("listings"),
        func.count(distinct(Listing.retailer_id)).label("retailers"),
        func.min(_buyable_price).label("min_price"),
        func.max(_buyable_price).label("max_price"),
    )
    .where(Listing.canonical_product_id.is_not(None), is_current)
    .group_by(Listing.canonical_product_id)
    .subquery()
)

# Every sort ends with id, so pages never shuffle between requests.
SORTS = {
    "name": (func.lower(CanonicalProduct.name).asc(), CanonicalProduct.id.asc()),
    "price_asc": (_stats.c.min_price.asc().nulls_last(), CanonicalProduct.id.asc()),
    "price_desc": (_stats.c.min_price.desc().nulls_last(), CanonicalProduct.id.asc()),
    "retailers": (_stats.c.retailers.desc(), _stats.c.min_price.asc().nulls_last(),
                  CanonicalProduct.id.asc()),
    "newest": (CanonicalProduct.created_at.desc(), CanonicalProduct.id.desc()),
}


def _product_query():
    """Products with at least one current listing, plus their stats."""
    return select(
        CanonicalProduct, _stats.c.listings, _stats.c.retailers,
        _stats.c.min_price, _stats.c.max_price,
    ).join(_stats, _stats.c.product_id == CanonicalProduct.id)


def _product_out(p: CanonicalProduct, listings=0, retailers=0, low=None, high=None) -> ProductOut:
    return ProductOut(
        id=p.id, name=p.name, brand=p.brand, category=p.category,
        product_type=p.product_type,
        specs=ProductSpecs(model=p.model, network=p.network, ram_gb=p.ram_gb,
                           storage_gb=p.storage_gb, package=p.package, ta_code=p.ta_code,
                           model_code=p.model_code, size_label=p.size_label),
        listings=listings, retailers=retailers, min_price=low, max_price=high,
        matching_version=p.matching_version,
    )


def _get_product(session: Session, product_id: int) -> ProductOut:
    product = session.get(CanonicalProduct, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    row = session.execute(
        _product_query().where(CanonicalProduct.id == product_id)
    ).first()
    return _product_out(*row) if row else _product_out(product)


def _offers(session: Session, product_id: int, current_only: bool = False) -> list[OfferOut]:
    """Linked listings, current ones first, each cheapest first."""
    current = is_current.label("current")
    stmt = (
        select(Listing, Retailer, current)
        .join(Retailer, Retailer.id == Listing.retailer_id)
        .where(Listing.canonical_product_id == product_id)
        .order_by(current.desc(), Listing.current_price.asc(), Listing.id.asc())
    )
    if current_only:
        stmt = stmt.where(is_current)
    return [
        OfferOut(
            listing_id=l.id, retailer=RetailerRef(id=r.id, name=r.name), name=l.name,
            url=l.url, price=l.current_price, availability=l.availability,
            box_note=l.box_note, last_seen_at=l.last_seen_at, current=bool(cur),
        )
        for l, r, cur in session.execute(stmt).all()
    ]


@router.get("/products", response_model=ProductPage)
def search_products(
    q: str | None = Query(None, max_length=100,
                          description="Every word must appear in the name, brand or model"),
    brand: str | None = Query(None, max_length=100),
    category: str | None = Query(None, max_length=100),
    product_type: str | None = Query(None, max_length=100),
    min_price: int | None = Query(None, ge=0, description="On the product's lowest price"),
    max_price: int | None = Query(None, ge=0, description="On the product's lowest price"),
    min_retailers: int = Query(1, ge=1, le=50,
                               description="2 = only products that can be compared"),
    sort: Literal["name", "price_asc", "price_desc", "retailers", "newest"] = "name",
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min_price cannot exceed max_price")

    stmt = _product_query().where(_stats.c.retailers >= min_retailers)
    text = func.concat_ws(" ", CanonicalProduct.name, CanonicalProduct.brand,
                          CanonicalProduct.model)
    for word in (q or "").split()[:MAX_QUERY_WORDS]:
        stmt = stmt.where(text.ilike(f"%{escape_like(word)}%", escape="\\"))
    if brand:
        stmt = stmt.where(func.lower(CanonicalProduct.brand) == brand.lower())
    if category:
        stmt = stmt.where(func.lower(CanonicalProduct.category) == category.lower())
    if product_type:
        stmt = stmt.where(func.lower(CanonicalProduct.product_type) == product_type.lower())
    if min_price is not None:
        stmt = stmt.where(_stats.c.min_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(_stats.c.min_price <= max_price)

    total = session.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = session.execute(stmt.order_by(*SORTS[sort]).limit(limit).offset(offset)).all()
    return ProductPage(
        total=total or 0, limit=limit, offset=offset,
        items=[_product_out(*row) for row in rows],
    )


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: ProductId, session: Session = Depends(get_session)):
    product = _get_product(session, product_id)
    return ProductDetail(**product.model_dump(), offers=_offers(session, product_id))


@router.get("/products/{product_id}/variants", response_model=list[ProductOut])
def product_variants(product_id: ProductId, session: Session = Depends(get_session)):
    """The same model in other RAM / storage, itself included, each with a current offer."""
    product = session.get(CanonicalProduct, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    rows = session.execute(
        _product_query()
        .where(CanonicalProduct.brand == product.brand,
               CanonicalProduct.model == product.model,
               CanonicalProduct.network.is_not_distinct_from(product.network),
               CanonicalProduct.package.is_not_distinct_from(product.package))
        .order_by(CanonicalProduct.ram_gb.asc().nulls_first(),
                  CanonicalProduct.storage_gb.asc().nulls_first(), CanonicalProduct.id)
    ).all()
    return [_product_out(*row) for row in rows]


@router.get("/products/{product_id}/prices", response_model=ProductPriceHistory)
def product_prices(product_id: ProductId, session: Session = Depends(get_session)):
    """Price history per linked listing, oldest point first."""
    offers = _offers(session, _get_product(session, product_id).id)
    points: dict[int, list[PricePoint]] = {o.listing_id: [] for o in offers}
    if points:
        for listing_id, price, availability, recorded_at in session.execute(
            select(PriceHistory.listing_id, PriceHistory.price,
                   PriceHistory.availability, PriceHistory.recorded_at)
            .where(PriceHistory.listing_id.in_(points))
            .order_by(PriceHistory.listing_id, PriceHistory.recorded_at, PriceHistory.id)
        ):
            points[listing_id].append(
                PricePoint(price=price, availability=availability, recorded_at=recorded_at))
    return ProductPriceHistory(
        product_id=product_id,
        listings=[ListingPrices(listing_id=o.listing_id, retailer=o.retailer,
                                points=points[o.listing_id]) for o in offers],
    )


@router.get("/compare/{product_id}", response_model=CompareOut)
def compare(product_id: ProductId, session: Session = Depends(get_session)):
    """The best current offer at each retailer, cheapest first.

    Only current listings take part (seen in the retailer's latest, recent
    scrape). "cheapest_listed" means cheapest of the retailers listed here,
    and only an offer that is not out of stock can be it. Ties are all marked.
    """
    product = _get_product(session, product_id)
    by_retailer: dict[int, list[OfferOut]] = {}
    for offer in _offers(session, product_id, current_only=True):
        by_retailer.setdefault(offer.retailer.id, []).append(offer)

    def rank(o: OfferOut):
        return (o.availability == OUT_OF_STOCK, o.price, o.listing_id)

    bests = {rid: min(offers, key=rank) for rid, offers in by_retailer.items()}
    buyable = [b.price for b in bests.values() if b.availability != OUT_OF_STOCK]
    low = min(buyable) if buyable else None
    rows = [
        RetailerOffer(
            retailer=best.retailer, best=best, offers=len(by_retailer[rid]),
            cheapest_listed=best.availability != OUT_OF_STOCK and best.price == low,
        )
        for rid, best in sorted(bests.items(), key=lambda kv: (*rank(kv[1])[:2], kv[1].retailer.name))
    ]
    not_listed = session.scalars(
        select(Retailer.name).where(Retailer.id.not_in(bests) if bests else True)
        .order_by(Retailer.id)
    ).all()
    return CompareOut(
        product=product, retailers=rows, not_listed=list(not_listed),
        spread=max(buyable) - low if len(buyable) >= 2 else None,
    )

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.deps import get_session
from api.schemas import BrandOut, ProductTypeOut, RetailerCount, RetailerOut
from db.models import Listing, ListingCategory, Retailer

router = APIRouter(tags=["catalog"])


@router.get("/retailers", response_model=list[RetailerOut])
def list_retailers(session: Session = Depends(get_session)):
    rows = session.execute(
        select(Retailer.id, Retailer.name, Retailer.base_url, func.count(Listing.id))
        .outerjoin(Listing, Listing.retailer_id == Retailer.id)
        .group_by(Retailer.id)
        .order_by(Retailer.id)
    ).all()
    return [
        RetailerOut(id=i, name=name, base_url=url, listings=count)
        for i, name, url, count in rows                                                                                                             
    ]


@router.get("/product-types", response_model=list[ProductTypeOut])
def list_product_types(session: Session = Depends(get_session)):
    """Canonical product types with listing counts, total and per retailer.

    Counts distinct listings, because one listing can have several category
    rows with the same type. Listings without a product type are not included.
    """
    rows = session.execute(
        select(
            ListingCategory.category,
            ListingCategory.product_type,
            Retailer.name,
            func.count(func.distinct(ListingCategory.listing_id)),
        )
        .join(Listing, Listing.id == ListingCategory.listing_id)
        .join(Retailer, Retailer.id == Listing.retailer_id)
        .where(ListingCategory.product_type.is_not(None))
        .group_by(ListingCategory.category, ListingCategory.product_type, Retailer.name)
    ).all()

    types: dict[tuple, ProductTypeOut] = {}
    for category, product_type, retailer, count in rows:
        item = types.setdefault(
            (category, product_type),
            ProductTypeOut(
                category=category, product_type=product_type, listings=0, retailers=[]
            ),
        )
        item.retailers.append(RetailerCount(retailer=retailer, listings=count))
        item.listings += count

    result = sorted(types.values(), key=lambda t: (t.category or "", t.product_type))
    for item in result:
        item.retailers.sort(key=lambda r: r.retailer)
    return result


@router.get("/brands", response_model=list[BrandOut])
def list_brands(session: Session = Depends(get_session)):
    """Brands with listing counts, most listings first. Unbranded listings are excluded."""
    rows = session.execute(
        select(Listing.brand, func.count(Listing.id))
        .where(Listing.brand.is_not(None))
        .group_by(Listing.brand)
        .order_by(func.count(Listing.id).desc(), Listing.brand)
    ).all()
    return [BrandOut(brand=brand, listings=count) for brand, count in rows]

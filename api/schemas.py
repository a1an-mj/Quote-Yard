from datetime import datetime

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str
    database: str
    listings: int


class RetailerOut(BaseModel):
    id: int
    name: str
    base_url: str | None
    listings: int


class RetailerCount(BaseModel):
    retailer: str
    listings: int


class ProductTypeOut(BaseModel):
    category: str | None
    product_type: str
    listings: int
    retailers: list[RetailerCount]


class BrandOut(BaseModel):
    brand: str
    listings: int


class CategoryOut(BaseModel):
    category: str | None
    product_type: str | None
    mapping_status: str
    raw_category: str
    raw_subcategory: str | None


class RetailerRef(BaseModel):
    id: int
    name: str


class ListingOut(BaseModel):
    id: int
    name: str
    url: str
    retailer: RetailerRef
    brand: str | None
    brand_status: str
    brand_candidates: list[str] | None
    price: int
    availability: str
    last_seen_at: datetime
    categories: list[CategoryOut]


class ListingDetail(ListingOut):
    first_seen_at: datetime
    taxonomy_version: str
    brands_version: str


class ListingPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ListingOut]


class CheapestOut(BaseModel):
    id: int
    name: str
    url: str
    price: int


class RetailerSummary(BaseModel):
    retailer: str
    listings: int
    min_price: int | None
    max_price: int | None
    cheapest: CheapestOut | None


class ListingSummary(BaseModel):
    total: int
    retailers: list[RetailerSummary]


class PricePoint(BaseModel):
    price: int
    availability: str
    recorded_at: datetime


class PriceHistoryOut(BaseModel):
    listing_id: int
    points: list[PricePoint]

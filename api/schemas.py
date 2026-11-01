from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, computed_field

from api.security import is_admin_email


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


class CategoryCount(BaseModel):
    category: str
    listings: int


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


# ---- Phase 5: canonical products --------------------------------------------

class ProductSpecs(BaseModel):
    model: str
    network: str | None
    ram_gb: int | None
    storage_gb: int | None
    package: str | None
    ta_code: str | None
    model_code: str | None = None
    size_label: str | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    brand: str
    category: str | None
    product_type: str | None
    specs: ProductSpecs
    listings: int
    retailers: int
    # Over listings that are not "Out of stock"; null when every listing is.
    min_price: int | None
    max_price: int | None
    matching_version: str


class ProductPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProductOut]


class OfferOut(BaseModel):
    source: Literal["scraped_listing"] = "scraped_listing"
    listing_id: int
    retailer: RetailerRef
    name: str
    url: str
    price: int
    availability: str
    box_note: str | None
    last_seen_at: datetime
    # Seen in the retailer's latest, recent scrape. Old offers are shown
    # for reference but never counted in prices or comparisons.
    current: bool


class ProductDetail(ProductOut):
    offers: list[OfferOut]


class ListingPrices(BaseModel):
    listing_id: int
    retailer: RetailerRef
    points: list[PricePoint]


class ProductPriceHistory(BaseModel):
    product_id: int
    listings: list[ListingPrices]


class RetailerOffer(BaseModel):
    retailer: RetailerRef
    best: OfferOut
    offers: int
    cheapest_listed: bool


class CompareOut(BaseModel):
    product: ProductOut
    # One row per retailer that lists the product, cheapest first.
    retailers: list[RetailerOffer]
    # Tracked retailers with no current linked listing. This means "not found
    # in our latest data", not "not sold there".
    not_listed: list[str]
    # Difference between the best offers of the listed retailers; null with
    # fewer than two retailers. Never against a list price.
    spread: int | None


# ---- accounts -----------------------------------------------------------------

class MessageOut(BaseModel):
    message: str


class UserOut(BaseModel):
    email: str
    first_name: str
    last_name: str | None
    created_at: datetime

    @computed_field
    @property
    def is_admin(self) -> bool:
        return is_admin_email(self.email)


class LocalOfferOut(BaseModel):
    """A local shop's own price. Labelled by source and never counted as a store's lowest price."""
    id: int
    source: Literal["verified_vendor"] = "verified_vendor"
    shop_name: str
    town: str
    district: str
    phone: str
    map_url: str
    price: int
    starts_on: date
    ends_on: date


class SavedOut(BaseModel):
    product: ProductOut
    price_when_saved: int | None
    saved_at: datetime


class AlertOut(BaseModel):
    product: ProductOut
    target_price: int
    last_notified_at: datetime | None
    created_at: datetime


class DealOut(BaseModel):
    kind: str  # price_drop | store_gap
    name: str
    brand: str | None
    retailer: str
    price: int
    # The earlier price (price_drop) or the next store's price (store_gap).
    compared_price: int
    compared_retailer: str | None
    saving: int
    label: str
    checked_at: datetime

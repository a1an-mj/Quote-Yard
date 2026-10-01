"""Quote Yard - Phase 3 database models (SQLAlchemy 2.0)."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

AVAILABILITY_VALUES = ("In stock", "Out of stock", "Unknown")
BRAND_STATUSES = ("matched", "unknown", "review")
MAPPING_STATUSES = ("mapped", "parent_only", "unmapped")


def _in(column: str, values: tuple) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Base(DeclarativeBase):
    pass


class Retailer(Base):
    __tablename__ = "retailers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    base_url: Mapped[str | None] = mapped_column(Text)

    listings: Mapped[list["Listing"]] = relationship(back_populates="retailer")


class CanonicalProduct(Base):
    """Created empty; filled in Phase 5 (product matching)."""

    __tablename__ = "canonical_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str | None] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    product_type: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Listing(Base):
    """One row per (retailer, url)."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    retailer_id: Mapped[int] = mapped_column(ForeignKey("retailers.id"))
    url: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)

    brand: Mapped[str | None] = mapped_column(Text)
    brand_status: Mapped[str] = mapped_column(Text)
    brand_candidates: Mapped[list | None] = mapped_column(JSONB(none_as_null=True))

    current_price: Mapped[int] = mapped_column(Integer)
    availability: Mapped[str] = mapped_column(Text)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    canonical_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("canonical_products.id")
    )
    taxonomy_version: Mapped[str] = mapped_column(Text)
    brands_version: Mapped[str] = mapped_column(Text)

    retailer: Mapped[Retailer] = relationship(back_populates="listings")
    categories: Mapped[list["ListingCategory"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("retailer_id", "url", name="uq_listings_retailer_url"),
        CheckConstraint("current_price > 0", name="ck_listings_price_positive"),
        CheckConstraint(
            _in("availability", AVAILABILITY_VALUES), name="ck_listings_availability"
        ),
        CheckConstraint(
            _in("brand_status", BRAND_STATUSES), name="ck_listings_brand_status"
        ),
        # matched <=> brand present; review <=> candidates present
        CheckConstraint(
            "(brand_status = 'matched') = (brand IS NOT NULL)",
            name="ck_listings_brand_matches_status",
        ),
        CheckConstraint(
            "(brand_status = 'review') = (brand_candidates IS NOT NULL)",
            name="ck_listings_candidates_match_status",
        ),
        Index("ix_listings_brand", "brand"),
        Index("ix_listings_canonical_product_id", "canonical_product_id"),
    )


class ListingCategory(Base):
    """One row per distinct (listing, raw_category, raw_subcategory)."""

    __tablename__ = "listing_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE")
    )
    category: Mapped[str | None] = mapped_column(Text)
    product_type: Mapped[str | None] = mapped_column(Text)
    mapping_status: Mapped[str] = mapped_column(Text)
    raw_category: Mapped[str] = mapped_column(Text)
    raw_subcategory: Mapped[str | None] = mapped_column(Text)

    listing: Mapped[Listing] = relationship(back_populates="categories")

    __table_args__ = (
        CheckConstraint(
            _in("mapping_status", MAPPING_STATUSES),
            name="ck_listing_categories_mapping_status",
        ),
        Index("ix_listing_categories_product_type", "product_type"),
        Index("ix_listing_categories_category", "category"),
    )


# NULL-safe uniqueness: two rows with the same listing, raw_category and a NULL
# raw_subcategory count as duplicates (works on every PostgreSQL version).
Index(
    "uq_listing_categories_pair",
    ListingCategory.listing_id,
    ListingCategory.raw_category,
    func.coalesce(ListingCategory.raw_subcategory, ""),
    unique=True,
)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE")
    )
    price: Mapped[int] = mapped_column(Integer)
    availability: Mapped[str] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    listing: Mapped[Listing] = relationship(back_populates="price_history")

    __table_args__ = (
        CheckConstraint("price > 0", name="ck_price_history_price_positive"),
        CheckConstraint(
            _in("availability", AVAILABILITY_VALUES),
            name="ck_price_history_availability",
        ),
    )


Index(
    "ix_price_history_listing_time",
    PriceHistory.listing_id,
    PriceHistory.recorded_at.desc(),
)
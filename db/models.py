"""Quote Yard - Phase 3 database models (SQLAlchemy 2.0)."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

AVAILABILITY_VALUES = ("In stock", "Out of stock", "Unknown")
BRAND_STATUSES = ("matched", "unknown", "review")
MAPPING_STATUSES = ("mapped", "parent_only", "unmapped")
NETWORK_VALUES = ("2G", "3G", "4G", "5G")
EMAIL_CODE_PURPOSES = ("verify_email", "reset_password")


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
    """One product that several retailer listings can point to (Phase 5).

    Filled by the matcher: match_key is the matcher's grouping key and is
    unique. Phones are keyed on specs (storage set) or, for feature phones
    with no specs, on the TA model code.
    """

    __tablename__ = "canonical_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    product_type: Mapped[str | None] = mapped_column(Text)

    model: Mapped[str] = mapped_column(Text)
    network: Mapped[str | None] = mapped_column(Text)
    ram_gb: Mapped[int | None] = mapped_column(Integer)
    storage_gb: Mapped[int | None] = mapped_column(Integer)
    package: Mapped[str | None] = mapped_column(Text)
    ta_code: Mapped[str | None] = mapped_column(Text)
    match_key: Mapped[str] = mapped_column(Text, unique=True)
    matching_version: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    listings: Mapped[list["Listing"]] = relationship(back_populates="canonical_product")

    __table_args__ = (
        CheckConstraint(
            _in("network", NETWORK_VALUES), name="ck_canonical_products_network"
        ),
        CheckConstraint("ram_gb > 0", name="ck_canonical_products_ram_positive"),
        CheckConstraint(
            "storage_gb > 0", name="ck_canonical_products_storage_positive"
        ),
        # every product is keyed on storage, or on a TA code when it has no specs
        CheckConstraint(
            "storage_gb IS NOT NULL OR ta_code IS NOT NULL",
            name="ck_canonical_products_has_key_spec",
        ),
        Index("ix_canonical_products_brand", "brand"),
        Index("ix_canonical_products_product_type", "product_type"),
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
    # Box contents that differ from the plain product ("without adapter");
    # set by the matcher, never part of the match key.
    box_note: Mapped[str | None] = mapped_column(Text)
    taxonomy_version: Mapped[str] = mapped_column(Text)
    brands_version: Mapped[str] = mapped_column(Text)

    retailer: Mapped[Retailer] = relationship(back_populates="listings")
    canonical_product: Mapped[CanonicalProduct | None] = relationship(
        back_populates="listings"
    )
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


class User(Base):
    """A customer account. email is stored casefolded."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    first_name: Mapped[str] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    # NULL until the sign-up code is entered; unverified accounts cannot log in.
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
    )


class EmailCode(Base):
    """A one-time emailed code, for sign-up verification and password reset."""

    __tablename__ = "email_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(Text)
    code_hash: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(_in("purpose", EMAIL_CODE_PURPOSES), name="ck_email_codes_purpose"),
        CheckConstraint("attempts >= 0", name="ck_email_codes_attempts"),
        Index("ix_email_codes_user_purpose", "user_id", "purpose"),
    )


class UserSession(Base):
    """A login. Only the token's hash is stored, so a database leak exposes no live session."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(Text, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("ix_user_sessions_user_id", "user_id"),)


class SavedProduct(Base):
    __tablename__ = "saved_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    canonical_product_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="CASCADE")
    )
    # Lowest current price when saved, for a later "dropped since you saved it".
    price_when_saved: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "canonical_product_id", name="uq_saved_products_user_product"),
    )


class PriceAlert(Base):
    """Email the user when the product's lowest current price goes below target_price."""

    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    canonical_product_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="CASCADE")
    )
    target_price: Mapped[int] = mapped_column(Integer)
    # The price last emailed about: mail again only for a lower one. Cleared
    # when the price climbs back to the target.
    last_notified_price: Mapped[int | None] = mapped_column(Integer)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "canonical_product_id", name="uq_price_alerts_user_product"),
        CheckConstraint("target_price > 0", name="ck_price_alerts_target_positive"),
    )

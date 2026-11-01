"""Local shops: accounts, one-time links, offers and an audit log. New tables only.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def _created():
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                     server_default=sa.func.now())


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("shop_name", sa.Text(), nullable=False),
        sa.Column("owner_name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("town", sa.Text(), nullable=False),
        sa.Column("district", sa.Text(), nullable=False),
        sa.Column("gst_number", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        _created(),
        sa.CheckConstraint("email = lower(email)", name="ck_vendors_email_lowercase"),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'suspended')",
                           name="ck_vendors_status"),
    )
    op.create_table(
        "vendor_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        _created(),
        sa.CheckConstraint("purpose IN ('invite', 'reset_password')",
                           name="ck_vendor_tokens_purpose"),
    )
    op.create_index("ix_vendor_tokens_email_purpose", "vendor_tokens", ["email", "purpose"])
    op.create_table(
        "vendor_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(),
                  sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        _created(),
    )
    op.create_index("ix_vendor_sessions_vendor_id", "vendor_sessions", ["vendor_id"])
    op.create_table(
        "vendor_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(),
                  sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canonical_product_id", sa.Integer(),
                  sa.ForeignKey("canonical_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("closed_by", sa.Text()),
        _created(),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.CheckConstraint("price > 0", name="ck_vendor_offers_price_positive"),
        sa.CheckConstraint("ends_on >= starts_on", name="ck_vendor_offers_dates"),
        sa.CheckConstraint("closed_by IN ('vendor', 'admin', 'replaced')",
                           name="ck_vendor_offers_closed_by"),
    )
    op.create_index("uq_vendor_offers_open", "vendor_offers", ["vendor_id", "canonical_product_id"],
                    unique=True, postgresql_where=sa.text("closed_at IS NULL"))
    op.create_index("ix_vendor_offers_product", "vendor_offers", ["canonical_product_id"])
    op.create_table(
        "vendor_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="SET NULL")),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("vendor_offers.id", ondelete="SET NULL")),
        sa.Column("detail", JSONB()),
        _created(),
    )


def downgrade() -> None:
    op.drop_table("vendor_audit_log")
    op.drop_table("vendor_offers")
    op.drop_table("vendor_sessions")
    op.drop_table("vendor_tokens")
    op.drop_table("vendors")

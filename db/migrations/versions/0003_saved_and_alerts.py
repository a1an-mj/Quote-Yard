"""Saved products and price alerts. New tables only.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-31
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _owner_columns():
    return [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canonical_product_id", sa.Integer(),
                  sa.ForeignKey("canonical_products.id", ondelete="CASCADE"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "saved_products",
        *_owner_columns(),
        sa.Column("price_when_saved", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "canonical_product_id",
                            name="uq_saved_products_user_product"),
    )
    op.create_table(
        "price_alerts",
        *_owner_columns(),
        sa.Column("target_price", sa.Integer(), nullable=False),
        sa.Column("last_notified_price", sa.Integer()),
        sa.Column("last_notified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "canonical_product_id",
                            name="uq_price_alerts_user_product"),
        sa.CheckConstraint("target_price > 0", name="ck_price_alerts_target_positive"),
    )


def downgrade() -> None:
    op.drop_table("price_alerts")
    op.drop_table("saved_products")

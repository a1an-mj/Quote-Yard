"""Index for "is this listing from its retailer's latest scrape?".

The check runs once per listing and scanned the whole table each time, which
grows as more product types are matched.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-01
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_listings_retailer_last_seen", "listings", ["retailer_id", "last_seen_at"])


def downgrade() -> None:
    op.drop_index("ix_listings_retailer_last_seen", table_name="listings")

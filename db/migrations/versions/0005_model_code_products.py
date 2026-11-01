"""Products matched on a manufacturer model code (Phase 9).

Adds model_code and size_label, and lets a product be keyed on its model code
instead of phone specs.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

TABLE = "canonical_products"
CONSTRAINT = "ck_canonical_products_has_key_spec"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column("model_code", sa.Text()))
    op.add_column(TABLE, sa.Column("size_label", sa.Text()))
    op.drop_constraint(CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(
        CONSTRAINT, TABLE,
        "storage_gb IS NOT NULL OR ta_code IS NOT NULL OR model_code IS NOT NULL",
    )


def downgrade() -> None:
    op.execute(f"UPDATE listings SET canonical_product_id = NULL WHERE canonical_product_id IN "
               f"(SELECT id FROM {TABLE} WHERE model_code IS NOT NULL)")
    op.execute(f"DELETE FROM {TABLE} WHERE model_code IS NOT NULL")
    op.drop_constraint(CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(
        CONSTRAINT, TABLE, "storage_gb IS NOT NULL OR ta_code IS NOT NULL",
    )
    op.drop_column(TABLE, "size_label")
    op.drop_column(TABLE, "model_code")

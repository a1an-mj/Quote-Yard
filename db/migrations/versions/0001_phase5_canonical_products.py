"""Phase 5: match columns on canonical_products, box_note on listings.

Starts from the Phase 3/4 schema made by create_all. canonical_products is
still empty at this point, so the new NOT NULL columns need no backfill;
the upgrade refuses to run if the table has rows.

Revision ID: 0001
Revises:
Create Date: 2026-10-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

CP = "canonical_products"


def upgrade() -> None:
    rows = op.get_bind().execute(sa.text(f"SELECT count(*) FROM {CP}")).scalar()
    if rows:
        raise RuntimeError(f"{CP} has {rows} rows; this migration expects it empty")

    op.alter_column(CP, "brand", existing_type=sa.Text(), nullable=False)
    op.add_column(CP, sa.Column("model", sa.Text(), nullable=False))
    op.add_column(CP, sa.Column("network", sa.Text()))
    op.add_column(CP, sa.Column("ram_gb", sa.Integer()))
    op.add_column(CP, sa.Column("storage_gb", sa.Integer()))
    op.add_column(CP, sa.Column("package", sa.Text()))
    op.add_column(CP, sa.Column("ta_code", sa.Text()))
    op.add_column(CP, sa.Column("match_key", sa.Text(), nullable=False))
    op.add_column(CP, sa.Column("matching_version", sa.Text(), nullable=False))

    op.create_unique_constraint("canonical_products_match_key_key", CP, ["match_key"])
    op.create_check_constraint(
        "ck_canonical_products_network", CP, "network IN ('2G', '3G', '4G', '5G')"
    )
    op.create_check_constraint("ck_canonical_products_ram_positive", CP, "ram_gb > 0")
    op.create_check_constraint(
        "ck_canonical_products_storage_positive", CP, "storage_gb > 0"
    )
    op.create_check_constraint(
        "ck_canonical_products_has_key_spec",
        CP,
        "storage_gb IS NOT NULL OR ta_code IS NOT NULL",
    )
    op.create_index("ix_canonical_products_brand", CP, ["brand"])
    op.create_index("ix_canonical_products_product_type", CP, ["product_type"])

    op.add_column("listings", sa.Column("box_note", sa.Text()))


def downgrade() -> None:
    op.drop_column("listings", "box_note")

    op.drop_index("ix_canonical_products_product_type", table_name=CP)
    op.drop_index("ix_canonical_products_brand", table_name=CP)
    for name in (
        "ck_canonical_products_has_key_spec",
        "ck_canonical_products_storage_positive",
        "ck_canonical_products_ram_positive",
        "ck_canonical_products_network",
    ):
        op.drop_constraint(name, CP, type_="check")
    op.drop_constraint("canonical_products_match_key_key", CP, type_="unique")
    for col in ("matching_version", "match_key", "ta_code", "package",
                "storage_gb", "ram_gb", "network", "model"):
        op.drop_column(CP, col)
    op.alter_column(CP, "brand", existing_type=sa.Text(), nullable=True)

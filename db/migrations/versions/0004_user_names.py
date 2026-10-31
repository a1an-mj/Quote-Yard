"""First name (required) and last name (optional) on users.

Accounts made before this get an empty first name, which the API never
accepts for new ones.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-01
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.Text(), nullable=False, server_default=""))
    op.alter_column("users", "first_name", server_default=None)
    op.add_column("users", sa.Column("last_name", sa.Text()))


def downgrade() -> None:
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")

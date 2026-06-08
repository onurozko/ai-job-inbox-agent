"""Add google profile fields to users

Revision ID: 003
Revises: 002
Create Date: 2026-06-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_sub", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("picture_url", sa.String(length=2048), nullable=True))
    op.create_index(op.f("ix_users_google_sub"), "users", ["google_sub"], unique=True)
    op.drop_column("users", "gmail_refresh_token")


def downgrade() -> None:
    op.add_column("users", sa.Column("gmail_refresh_token", sa.Text(), nullable=True))
    op.drop_index(op.f("ix_users_google_sub"), table_name="users")
    op.drop_column("users", "picture_url")
    op.drop_column("users", "google_sub")

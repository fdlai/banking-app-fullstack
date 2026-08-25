"""users id to uuid

Revision ID: 3c26ee5fc9f3
Revises: a71b0709dfcd
Create Date: 2026-08-25

Replaces the sequential integer primary key with a random UUID. Postgres
cannot cast integer -> uuid, so existing ids cannot be preserved: every row
is assigned a fresh gen_random_uuid(). Reseed afterwards with
`python -m data.seed`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c26ee5fc9f3'
down_revision: Union[str, Sequence[str], None] = 'a71b0709dfcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("users", "id")
    op.add_column(
        "users",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.create_primary_key("users_pkey", "users", ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    # SERIAL both creates the sequence and backfills existing rows, which a
    # plain add_column of a NOT NULL integer cannot do.
    op.drop_column("users", "id")
    op.execute("ALTER TABLE users ADD COLUMN id SERIAL PRIMARY KEY")

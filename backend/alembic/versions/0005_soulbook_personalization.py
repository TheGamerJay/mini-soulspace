"""SoulBook personalization (Phase 4.1).

Revision ID: 0005_soulbook_personalization
Revises: 0004_memory_intelligence
Create Date: 2026-07-07
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_soulbook_personalization"
down_revision: str | None = "0004_memory_intelligence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("soul_books", sa.Column("cover_color", sa.String(length=20), server_default="#6d5bd0", nullable=False))
    op.add_column("soul_books", sa.Column("cover_material", sa.String(length=30), server_default="leather", nullable=False))
    op.add_column("soul_books", sa.Column("icon", sa.String(length=16), server_default="📔", nullable=False))
    op.add_column("soul_books", sa.Column("category", sa.String(length=50), nullable=True))
    op.add_column("soul_books", sa.Column("ribbon_color", sa.String(length=20), server_default="#e0b64c", nullable=False))
    op.add_column("soul_books", sa.Column("is_favorite", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("soul_books", sa.Column("shelf_position", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_soul_books_is_favorite"), "soul_books", ["is_favorite"])


def downgrade() -> None:
    op.drop_index(op.f("ix_soul_books_is_favorite"), table_name="soul_books")
    for col in ("shelf_position", "is_favorite", "ribbon_color", "category", "icon", "cover_material", "cover_color"):
        op.drop_column("soul_books", col)

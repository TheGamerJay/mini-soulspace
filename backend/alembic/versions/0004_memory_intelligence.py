"""Memory Intelligence: provenance columns + version history.

Revision ID: 0004_memory_intelligence
Revises: 0003_soul_memories
Create Date: 2026-07-06
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_memory_intelligence"
down_revision: str | None = "0003_soul_memories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("soul_memories", sa.Column("confidence", sa.Float(), server_default="0.6", nullable=False))
    op.add_column("soul_memories", sa.Column("source", sa.String(length=30), server_default="souldiary", nullable=False))
    op.add_column("soul_memories", sa.Column("evidence", sa.Text(), nullable=True))
    op.add_column("soul_memories", sa.Column("verification_status", sa.String(length=30), server_default="unverified", nullable=False))
    op.add_column("soul_memories", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("soul_memories", sa.Column("version", sa.Integer(), server_default="1", nullable=False))

    op.create_table(
        "soul_memory_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("memory_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column("confidence", sa.Float(), server_default="0.6", nullable=False),
        sa.Column("reason_changed", sa.String(length=100), nullable=False),
        sa.Column("author", sa.String(length=20), server_default="system", nullable=False),
        sa.Column("is_outdated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["memory_id"], ["soul_memories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_soul_memory_versions_memory_id"), "soul_memory_versions", ["memory_id"])


def downgrade() -> None:
    op.drop_table("soul_memory_versions")
    op.drop_column("soul_memories", "version")
    op.drop_column("soul_memories", "last_verified_at")
    op.drop_column("soul_memories", "verification_status")
    op.drop_column("soul_memories", "evidence")
    op.drop_column("soul_memories", "source")
    op.drop_column("soul_memories", "confidence")

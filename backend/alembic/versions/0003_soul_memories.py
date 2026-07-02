"""Long-term memory store (soul_memories).

Revision ID: 0003_soul_memories
Revises: 0002_soulbook_engine
Create Date: 2026-07-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_soul_memories"
down_revision: str | None = "0002_soulbook_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "soul_memories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("memory_type", sa.String(length=30), nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="medium", nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), server_default="", nullable=False),
        sa.Column("keywords", sa.String(length=500), nullable=True),
        sa.Column("related_to_id", sa.Uuid(), nullable=True),
        sa.Column("source_ref", sa.String(length=200), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_referenced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_to_id"], ["soul_memories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_soul_memories_user_id"), "soul_memories", ["user_id"])
    op.create_index(op.f("ix_soul_memories_memory_type"), "soul_memories", ["memory_type"])
    op.create_index(op.f("ix_soul_memories_priority"), "soul_memories", ["priority"])
    op.create_index(op.f("ix_soul_memories_is_deleted"), "soul_memories", ["is_deleted"])
    op.create_index(op.f("ix_soul_memories_is_archived"), "soul_memories", ["is_archived"])


def downgrade() -> None:
    op.drop_table("soul_memories")

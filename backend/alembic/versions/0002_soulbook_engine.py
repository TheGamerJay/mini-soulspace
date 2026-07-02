"""SoulBook Engine: books, chapters, pages, bookmarks, recents.

Revision ID: 0002_soulbook_engine
Revises: 0001_auth_foundation
Create Date: 2026-07-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_soulbook_engine"
down_revision: str | None = "0001_auth_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "soul_books",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("cover_style", sa.String(length=40), server_default="classic", nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_soul_books_user_id"), "soul_books", ["user_id"])
    op.create_index(op.f("ix_soul_books_title"), "soul_books", ["title"])
    op.create_index(op.f("ix_soul_books_is_archived"), "soul_books", ["is_archived"])
    op.create_index(op.f("ix_soul_books_is_deleted"), "soul_books", ["is_deleted"])

    op.create_table(
        "soul_chapters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("chapter_number", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["soul_books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_soul_chapters_user_id"), "soul_chapters", ["user_id"])
    op.create_index(op.f("ix_soul_chapters_book_id"), "soul_chapters", ["book_id"])
    op.create_index(op.f("ix_soul_chapters_title"), "soul_chapters", ["title"])
    op.create_index(op.f("ix_soul_chapters_is_deleted"), "soul_chapters", ["is_deleted"])

    op.create_table(
        "soul_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("chapter_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("content", sa.Text(), server_default="", nullable=False),
        sa.Column("page_number", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("content_format", sa.String(length=20), server_default="markdown", nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("word_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("character_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["soul_books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["soul_chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_soul_pages_user_id"), "soul_pages", ["user_id"])
    op.create_index(op.f("ix_soul_pages_book_id"), "soul_pages", ["book_id"])
    op.create_index(op.f("ix_soul_pages_chapter_id"), "soul_pages", ["chapter_id"])
    op.create_index(op.f("ix_soul_pages_title"), "soul_pages", ["title"])
    op.create_index(op.f("ix_soul_pages_is_deleted"), "soul_pages", ["is_deleted"])

    op.create_table(
        "soul_bookmarks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("chapter_id", sa.Uuid(), nullable=True),
        sa.Column("page_id", sa.Uuid(), nullable=True),
        sa.Column("label", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["soul_books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["soul_chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["page_id"], ["soul_pages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_soul_bookmarks_user_id"), "soul_bookmarks", ["user_id"])

    op.create_table(
        "soul_recent_books",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["soul_books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id"),
    )
    op.create_index(op.f("ix_soul_recent_books_user_id"), "soul_recent_books", ["user_id"])

    op.create_table(
        "soul_recent_chapters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("chapter_id", sa.Uuid(), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["soul_books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["soul_chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chapter_id"),
    )
    op.create_index(op.f("ix_soul_recent_chapters_user_id"), "soul_recent_chapters", ["user_id"])


def downgrade() -> None:
    op.drop_table("soul_recent_chapters")
    op.drop_table("soul_recent_books")
    op.drop_table("soul_bookmarks")
    op.drop_table("soul_pages")
    op.drop_table("soul_chapters")
    op.drop_table("soul_books")

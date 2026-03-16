"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(200), nullable=False),
        sa.Column("role", sa.String(20), server_default="viewer", nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    # Bulletins
    op.create_table(
        "bulletins",
        sa.Column("id", sa.String(20), nullable=False),
        sa.Column("date", sa.String(50), nullable=False),
        sa.Column("lesson_code", sa.String(20), nullable=True),
        sa.Column("lesson_title", sa.String(200), nullable=True),
        sa.Column("sabbath_ends", sa.String(20), nullable=True),
        sa.Column("next_sabbath", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Program Items
    op.create_table(
        "program_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bulletin_id", sa.String(20), nullable=False),
        sa.Column("block", sa.String(30), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("note", sa.String(200), nullable=True),
        sa.Column("person", sa.String(200), nullable=True),
        sa.Column("is_sermon", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.ForeignKeyConstraint(["bulletin_id"], ["bulletins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Coordinators
    op.create_table(
        "coordinators",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bulletin_id", sa.String(20), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["bulletin_id"], ["bulletins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Announcements
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("bulletin_id", sa.String(20), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("recurring", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("pinned", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.ForeignKeyConstraint(["bulletin_id"], ["bulletins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Calendar Events
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("day", sa.String(20), nullable=False),
        sa.Column("time", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Members
    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Member Roles
    op.create_table(
        "member_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Teams
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Groups
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Contacts
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("email", sa.String(100), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("contacts")
    op.drop_table("groups")
    op.drop_table("teams")
    op.drop_table("member_roles")
    op.drop_table("members")
    op.drop_table("calendar_events")
    op.drop_table("announcements")
    op.drop_table("coordinators")
    op.drop_table("program_items")
    op.drop_table("bulletins")
    op.drop_table("users")

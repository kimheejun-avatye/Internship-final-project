"""Create users, rooms, refresh_token and reservations.

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

team = postgresql.ENUM("AVATYE", "GURU", name="user_team", create_type=False)
role = postgresql.ENUM("ADMIN", "MEMBER", name="user_role", create_type=False)
status = postgresql.ENUM("ACTIVE", "BLOCK", name="room_status", create_type=False)


def upgrade():
    for enum in (team, role, status):
        enum.create(op.get_bind(), checkfirst=False)

    op.create_table(
        "users",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("team", team, nullable=False),
        sa.Column("role", role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "rooms",
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", status, nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("room_id", name="pk_rooms"),
    )
    op.create_table(
        "refresh_token",
        sa.Column("token_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("Refresh_token", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token_id", name="pk_refresh_token"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_refresh_token_user"),
    )
    op.create_table(
        "reservations",
        sa.Column("reservation_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("participants", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("reservation_id", name="pk_reservations"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.room_id"], name="fk_reservations_room"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], name="fk_reservations_user"),
    )


def downgrade():
    for table in ("reservations", "refresh_token", "rooms", "users"):
        op.drop_table(table)
    for enum in (status, role, team):
        enum.drop(op.get_bind(), checkfirst=False)

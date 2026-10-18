"""Server sessions, login limits, reset verification, and globally unique email.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # Fail rather than silently discard existing duplicates.
    op.create_index("users_email_uniq", "users", ["email"], unique=True)
    op.drop_index("users_email_active_uniq", table_name="users")
    op.create_table(
        "user_sessions",
        sa.Column(
            "session_id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("csrf_token", sa.Text(), nullable=False),
        *[
            sa.Column(c, sa.DateTime(timezone=True), nullable=False)
            for c in (
                "created_at",
                "last_activity_at",
                "idle_expires_at",
                "absolute_expires_at",
            )
        ],
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_table(
        "login_failures",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email_key", sa.Text(), nullable=False),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_login_failures_email_time", "login_failures", ["email_key", "failed_at"]
    )
    op.create_table(
        "login_locks",
        sa.Column("email_key", sa.Text(), primary_key=True),
        sa.Column("blocked_until", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "login_ip_requests",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("ip_key", sa.Text(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_login_ip_requests_key_time", "login_ip_requests", ["ip_key", "requested_at"]
    )
    op.create_table(
        "password_reset_verifications",
        sa.Column("email", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.user_id")),
        sa.Column("code_hash", sa.Text()),
        sa.Column("code_expires_at", sa.DateTime(timezone=True)),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("reset_token_hash", sa.Text(), unique=True),
        sa.Column("reset_token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    for table in (
        "password_reset_verifications",
        "login_ip_requests",
        "login_locks",
        "login_failures",
        "user_sessions",
    ):
        op.drop_table(table)
    op.create_index(
        "users_email_active_uniq",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("blocked_at IS NULL"),
    )
    op.drop_index("users_email_uniq", table_name="users")

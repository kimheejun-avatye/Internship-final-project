"""Signup: users columns/constraints and email verification tables.

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE user_team RENAME TO team_type")
    op.execute("ALTER TYPE user_role RENAME TO role_type")

    # 0001 에 name 이 이미 있으면(최신 0001) 건너뛴다. 예전 0001 로 만든 DB 에는 임시 기본값으로 추가한다
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE users ALTER COLUMN name DROP DEFAULT")
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("phone", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    # 기존 회원은 이미 이용 중이므로 승인된 것으로 본다
    op.execute("UPDATE users SET approved_at = created_at AT TIME ZONE 'UTC'")

    for column in ("created_at", "updated_at"):
        op.alter_column(
            "users",
            column,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
    op.alter_column("users", "user_id", server_default=sa.text("gen_random_uuid()"))
    op.alter_column("users", "role", server_default="MEMBER")
    op.alter_column("users", "created_at", server_default=sa.text("now()"))

    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.create_index(
        "users_email_active_uniq",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("blocked_at IS NULL"),
    )
    op.create_check_constraint("users_email_normalized", "users", "email = lower(btrim(email))")
    op.create_check_constraint("users_phone_format", "users", r"phone ~ '^01[016789][0-9]{7,8}$'")

    op.create_table(
        "email_verifications",
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("code_hash", sa.Text(), nullable=True),
        sa.Column("code_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signup_token_hash", sa.Text(), nullable=True),
        sa.Column("signup_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("email", name="pk_email_verifications"),
    )
    op.create_table(
        "email_send_log",
        sa.Column("log_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("ip", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("failed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("log_id", name="pk_email_send_log"),
    )
    op.create_index("email_send_log_email_sent_at", "email_send_log", ["email", "sent_at"])
    op.create_index("email_send_log_ip_sent_at", "email_send_log", ["ip", "sent_at"])
    op.create_table(
        "signup_check_log",
        sa.Column("log_id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ip", sa.Text(), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("log_id", name="pk_signup_check_log"),
    )
    op.create_index("signup_check_log_ip_checked_at", "signup_check_log", ["ip", "checked_at"])


def downgrade():
    op.drop_table("signup_check_log")
    op.drop_table("email_send_log")
    op.drop_table("email_verifications")

    op.drop_constraint("users_phone_format", "users", type_="check")
    op.drop_constraint("users_email_normalized", "users", type_="check")
    op.drop_index("users_email_active_uniq", table_name="users")
    op.create_unique_constraint("uq_users_email", "users", ["email"])

    op.alter_column("users", "created_at", server_default=None)
    op.alter_column("users", "role", server_default=None)
    op.alter_column("users", "user_id", server_default=None)
    for column in ("created_at", "updated_at"):
        op.alter_column(
            "users",
            column,
            type_=sa.DateTime(timezone=False),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
    for column in ("approved_at", "phone", "birth_date"):  # name 은 0001 소유이므로 남긴다
        op.drop_column("users", column)

    op.execute("ALTER TYPE role_type RENAME TO user_role")
    op.execute("ALTER TYPE team_type RENAME TO user_team")

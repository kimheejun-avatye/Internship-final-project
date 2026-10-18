"""Calendar: reservation attendees and Slack reminders.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


reminder_status = postgresql.ENUM(
    "PENDING",
    "PROCESSING",
    "SENT",
    "FAILED",
    "CANCELLED",
    name="reminder_status",
    create_type=False,
)


def upgrade():
    # 예약 참석자
    op.create_table(
        "reservation_attendees",
        sa.Column(
            "reservation_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "reservation_id",
            "user_id",
            name="pk_reservation_attendees",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservations.reservation_id"],
            name="fk_reservation_attendees_reservation",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name="fk_reservation_attendees_user",
        ),
    )

    op.create_index(
        "ix_reservation_attendees_user_id",
        "reservation_attendees",
        ["user_id"],
    )

    # PostgreSQL ENUM을 테이블 생성 전에 명시적으로 생성
    reminder_status.create(op.get_bind(), checkfirst=False)

    # 참석자별 슬랙 리마인더
    op.create_table(
        "slack_reminders",
        sa.Column(
            "reminder_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "reservation_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "slack_channel_id",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "status",
            reminder_status,
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "claimed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint(
            "reminder_id",
            name="pk_slack_reminders",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_id", "user_id"],
            [
                "reservation_attendees.reservation_id",
                "reservation_attendees.user_id",
            ],
            name="fk_slack_reminders_attendee",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "reservation_id",
            "user_id",
            name="uq_slack_reminders_attendee",
        ),
    )

    op.create_index(
        "ix_slack_reminders_status_scheduled",
        "slack_reminders",
        ["status", "scheduled_at"],
    )


def downgrade():
    # 참조하는 자식 테이블부터 제거
    op.drop_index(
        "ix_slack_reminders_status_scheduled",
        table_name="slack_reminders",
    )
    op.drop_table("slack_reminders")

    # ENUM을 사용하는 테이블을 제거한 뒤 타입 제거
    reminder_status.drop(op.get_bind(), checkfirst=False)

    op.drop_index(
        "ix_reservation_attendees_user_id",
        table_name="reservation_attendees",
    )
    op.drop_table("reservation_attendees")
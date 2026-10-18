"""Join existing login and team calendar migration histories without changing data.

Revision ID: merge_0004
Revises: login_0003, 0003
"""

revision = "merge_0004"
down_revision = ("login_0003", "0003")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

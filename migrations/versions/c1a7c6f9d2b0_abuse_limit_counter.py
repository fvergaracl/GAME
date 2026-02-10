"""abuse_limit_counter table added

Revision ID: c1a7c6f9d2b0
Revises: 5b582dc38109
Create Date: 2026-02-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c1a7c6f9d2b0"
down_revision = "5b582dc38109"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "abuse_limit_counter",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopeType", sa.String(), nullable=False),
        sa.Column("scopeValue", sa.String(), nullable=False),
        sa.Column("windowName", sa.String(), nullable=False),
        sa.Column("windowStart", sa.DateTime(timezone=True), nullable=False),
        sa.Column("counter", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "scopeType",
            "scopeValue",
            "windowName",
            "windowStart",
            name="uq_abuse_limit_counter_scope_window",
        ),
    )
    op.create_index(
        op.f("ix_abuse_limit_counter_id"),
        "abuse_limit_counter",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_abuse_limit_counter_lookup",
        "abuse_limit_counter",
        ["scopeType", "scopeValue", "windowName", "windowStart"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_abuse_limit_counter_lookup", table_name="abuse_limit_counter")
    op.drop_index(op.f("ix_abuse_limit_counter_id"), table_name="abuse_limit_counter")
    op.drop_table("abuse_limit_counter")

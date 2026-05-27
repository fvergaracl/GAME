"""strategy_execution_log table added

Revision ID: f9d3a8c5b2e1
Revises: e1c8d5a4b9f7
Create Date: 2026-05-27 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f9d3a8c5b2e1"
down_revision = "e1c8d5a4b9f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "strategyexecutionlog",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("apiKey_used", sa.String(), nullable=True),
        sa.Column("oauth_user_id", sa.String(), nullable=True),
        sa.Column("strategyId", sa.String(), nullable=False),
        sa.Column("strategyVersion", sa.Integer(), nullable=False),
        sa.Column("strategyType", sa.String(), nullable=False),
        sa.Column("realmId", sa.String(), nullable=True),
        sa.Column("externalGameId", sa.String(), nullable=True),
        sa.Column("externalTaskId", sa.String(), nullable=True),
        sa.Column("externalUserId", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("errorCode", sa.String(), nullable=True),
        sa.Column("points", sa.Numeric(), nullable=True),
        sa.Column("caseName", sa.String(), nullable=True),
        sa.Column("durationMs", sa.Numeric(), nullable=False),
        sa.Column("nodesExecuted", sa.Integer(), nullable=False),
        sa.Column(
            "trace",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "sampled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("parentStrategyId", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["apiKey_used"], ["apikey.apiKey"]),
        sa.ForeignKeyConstraint(
            ["oauth_user_id"], ["oauthusers.provider_user_id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_strategyexecutionlog_id"),
        "strategyexecutionlog",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strategyexecutionlog_strategyId"),
        "strategyexecutionlog",
        ["strategyId"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strategyexecutionlog_realmId"),
        "strategyexecutionlog",
        ["realmId"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strategyexecutionlog_status"),
        "strategyexecutionlog",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strategyexecutionlog_sampled"),
        "strategyexecutionlog",
        ["sampled"],
        unique=False,
    )
    # Composite index for the runbook lookup
    # "last failed runs of strategy X" -- the dashboard surfaces this
    # ordered by created_at so the index lines the rows up in the same
    # order the page paginates.
    op.create_index(
        "ix_strategyexecutionlog_strategy_status_created",
        "strategyexecutionlog",
        ["strategyId", "status", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_strategyexecutionlog_strategy_status_created",
        table_name="strategyexecutionlog",
    )
    op.drop_index(
        op.f("ix_strategyexecutionlog_sampled"),
        table_name="strategyexecutionlog",
    )
    op.drop_index(
        op.f("ix_strategyexecutionlog_status"),
        table_name="strategyexecutionlog",
    )
    op.drop_index(
        op.f("ix_strategyexecutionlog_realmId"),
        table_name="strategyexecutionlog",
    )
    op.drop_index(
        op.f("ix_strategyexecutionlog_strategyId"),
        table_name="strategyexecutionlog",
    )
    op.drop_index(
        op.f("ix_strategyexecutionlog_id"),
        table_name="strategyexecutionlog",
    )
    op.drop_table("strategyexecutionlog")

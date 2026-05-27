"""export_audit_log table added

Revision ID: d7a4b0e2f1c9
Revises: 3a7e5c1b9d2f
Create Date: 2026-05-27 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d7a4b0e2f1c9"
down_revision = "3a7e5c1b9d2f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "exportauditlog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("apiKey_used", sa.String(), nullable=True),
        sa.Column("oauth_user_id", sa.String(), nullable=True),
        sa.Column("datasetType", sa.String(), nullable=False),
        sa.Column("format", sa.String(), nullable=False),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("rowLimit", sa.Integer(), nullable=False),
        sa.Column(
            "rowCount",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("-1"),
        ),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default=sa.text("'started'"),
        ),
        sa.Column("requestedBy", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["apiKey_used"], ["apikey.apiKey"]),
        sa.ForeignKeyConstraint(
            ["oauth_user_id"], ["oauthusers.provider_user_id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_exportauditlog_id"),
        "exportauditlog",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_exportauditlog_dataset_created",
        "exportauditlog",
        ["datasetType", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_exportauditlog_dataset_created", table_name="exportauditlog"
    )
    op.drop_index(
        op.f("ix_exportauditlog_id"), table_name="exportauditlog"
    )
    op.drop_table("exportauditlog")

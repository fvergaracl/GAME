"""strategy_definition table added

Revision ID: e1c8d5a4b9f7
Revises: d7a4b0e2f1c9
Create Date: 2026-05-27 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e1c8d5a4b9f7"
down_revision = "d7a4b0e2f1c9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "strategydefinition",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("apiKey_used", sa.String(), nullable=True),
        sa.Column("oauth_user_id", sa.String(), nullable=True),
        sa.Column("realmId", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "type",
            sa.String(),
            nullable=False,
            server_default=sa.text("'DSL_FULL'"),
        ),
        sa.Column("parentStrategyId", sa.String(), nullable=True),
        sa.Column(
            "astJson",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("blocklyXml", sa.Text(), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column("createdBy", sa.String(), nullable=True),
        sa.Column("publishedAt", sa.DateTime(timezone=True), nullable=True),
        sa.Column("experimentTag", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["apiKey_used"], ["apikey.apiKey"]),
        sa.ForeignKeyConstraint(["oauth_user_id"], ["oauthusers.provider_user_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "realmId",
            "name",
            "version",
            name="uq_strategydefinition_realm_name_version",
        ),
    )
    op.create_index(
        op.f("ix_strategydefinition_id"),
        "strategydefinition",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strategydefinition_realmId"),
        "strategydefinition",
        ["realmId"],
        unique=False,
    )
    op.create_index(
        op.f("ix_strategydefinition_status"),
        "strategydefinition",
        ["status"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_strategydefinition_status"),
        table_name="strategydefinition",
    )
    op.drop_index(
        op.f("ix_strategydefinition_realmId"),
        table_name="strategydefinition",
    )
    op.drop_index(
        op.f("ix_strategydefinition_id"),
        table_name="strategydefinition",
    )
    op.drop_table("strategydefinition")

"""ouath and logs table added

Revision ID: 8559703645d0
Revises: a034877f5226
Create Date: 2024-11-18 11:46:21.653421

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8559703645d0"
down_revision = "a034877f5226"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "oauthusers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("provider_user_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("apiKey_used", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["apiKey_used"],
            ["apikey.apiKey"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_user_id"),
    )
    op.create_index(op.f("ix_oauthusers_id"), "oauthusers", ["id"], unique=False)
    op.create_table(
        "logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("apiKey_used", sa.String(), nullable=True),
        sa.Column("oauth_user_id", sa.String(), nullable=True),
        sa.Column("log_level", sa.String(), nullable=True),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("module", sa.String(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["apiKey_used"],
            ["apikey.apiKey"],
        ),
        sa.ForeignKeyConstraint(
            ["oauth_user_id"],
            ["oauthusers.provider_user_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_logs_id"), "logs", ["id"], unique=False)

    op.add_column("apirequests", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("games", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("gamesparams", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("kpimetrics", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("tasks", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("tasksparams", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("uptimelogs", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("useractions", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column(
        "userinteractions", sa.Column("oauth_user_id", sa.String(), nullable=True)
    )
    op.add_column("userpoints", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("users", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column("wallet", sa.Column("oauth_user_id", sa.String(), nullable=True))
    op.add_column(
        "wallettransactions", sa.Column("oauth_user_id", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("wallettransactions", "oauth_user_id")
    op.drop_column("wallet", "oauth_user_id")
    op.drop_column("users", "oauth_user_id")
    op.drop_column("userpoints", "oauth_user_id")
    op.drop_column("userinteractions", "oauth_user_id")
    op.drop_column("useractions", "oauth_user_id")
    op.drop_column("uptimelogs", "oauth_user_id")
    op.drop_column("tasksparams", "oauth_user_id")
    op.drop_column("tasks", "oauth_user_id")
    op.drop_column("kpimetrics", "oauth_user_id")
    op.drop_column("gamesparams", "oauth_user_id")
    op.drop_column("games", "oauth_user_id")
    op.drop_column("apirequests", "oauth_user_id")
    op.drop_index(op.f("ix_oauthusers_id"), table_name="oauthusers")
    op.drop_table("oauthusers")
    op.drop_index(op.f("ix_logs_id"), table_name="logs")
    op.drop_table("logs")
    # ### end Alembic commands ###

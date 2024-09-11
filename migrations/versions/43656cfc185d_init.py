"""init

Revision ID: 43656cfc185d
Revises: 
Create Date: 2024-03-12 11:42:31.842819

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "43656cfc185d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "games",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("externalGameId", sa.String(), nullable=True),
        sa.Column("strategyId", sa.String(), nullable=True),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("endDateTime", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("externalGameId"),
    )
    op.create_index(op.f("ix_games_id"), "games", ["id"], unique=False)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("externalUserId", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("externalUserId"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_table(
        "gamesparams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("gameId", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["gameId"],
            ["games.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_gamesparams_id"), "gamesparams", ["id"], unique=False)
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("externalTaskId", sa.String(), nullable=True),
        sa.Column("gameId", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("strategyId", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["gameId"],
            ["games.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_id"), "tasks", ["id"], unique=False)
    op.create_table(
        "wallet",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("coinsBalance", sa.Float(), nullable=True),
        sa.Column("pointsBalance", sa.Float(), nullable=True),
        sa.Column("conversionRate", sa.Integer(), nullable=True),
        sa.Column("userId", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["userId"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("userId"),
    )
    op.create_index(op.f("ix_wallet_id"), "wallet", ["id"], unique=False)
    op.create_table(
        "tasksparams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("taskId", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["taskId"],
            ["tasks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasksparams_id"), "tasksparams", ["id"], unique=False)
    op.create_table(
        "userpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("userId", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("taskId", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["taskId"],
            ["tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["userId"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_userpoints_id"), "userpoints", ["id"], unique=False)
    op.create_table(
        "wallettransactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("transactionType", sa.String(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("coins", sa.Float(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("appliedConversionRate", sa.Float(), nullable=True),
        sa.Column("walletId", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["walletId"],
            ["wallet.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_wallettransactions_id"), "wallettransactions", ["id"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_wallettransactions_id"), table_name="wallettransactions")
    op.drop_table("wallettransactions")
    op.drop_index(op.f("ix_userpoints_id"), table_name="userpoints")
    op.drop_table("userpoints")
    op.drop_index(op.f("ix_tasksparams_id"), table_name="tasksparams")
    op.drop_table("tasksparams")
    op.drop_index(op.f("ix_wallet_id"), table_name="wallet")
    op.drop_table("wallet")
    op.drop_index(op.f("ix_tasks_id"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_gamesparams_id"), table_name="gamesparams")
    op.drop_table("gamesparams")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_games_id"), table_name="games")
    op.drop_table("games")
    # ### end Alembic commands ###

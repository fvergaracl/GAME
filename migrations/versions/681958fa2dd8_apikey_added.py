"""apiKey added

Revision ID: 681958fa2dd8
Revises: 59843af22ade
Create Date: 2024-09-10 11:18:40.943153

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "681958fa2dd8"
down_revision = "59843af22ade"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "apikey",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("apiKey", sa.String(), nullable=True),
        sa.Column("client", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("createdBy", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("apiKey"),
    )
    op.create_index(op.f("ix_apikey_id"), "apikey", ["id"], unique=False)
    op.add_column("games", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "games", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column("gamesparams", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "gamesparams", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column("tasks", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "tasks", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column("tasksparams", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "tasksparams", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column("useractions", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "useractions", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column("userpoints", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "userpoints", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column("users", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "users", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column("wallet", sa.Column("apiKey_used", sa.String(), nullable=True))
    op.create_foreign_key(None, "wallet", "apikey", ["apiKey_used"], ["apiKey"])
    op.add_column(
        "wallettransactions", sa.Column("apiKey_used", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        None, "wallettransactions", "apikey", ["apiKey_used"], ["apiKey"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "wallettransactions", type_="foreignkey")
    op.drop_column("wallettransactions", "apiKey_used")
    op.drop_constraint(None, "wallet", type_="foreignkey")
    op.drop_column("wallet", "apiKey_used")
    op.drop_constraint(None, "users", type_="foreignkey")
    op.drop_column("users", "apiKey_used")
    op.drop_constraint(None, "userpoints", type_="foreignkey")
    op.drop_column("userpoints", "apiKey_used")
    op.drop_constraint(None, "useractions", type_="foreignkey")
    op.drop_column("useractions", "apiKey_used")
    op.drop_constraint(None, "tasksparams", type_="foreignkey")
    op.drop_column("tasksparams", "apiKey_used")
    op.drop_constraint(None, "tasks", type_="foreignkey")
    op.drop_column("tasks", "apiKey_used")
    op.drop_constraint(None, "gamesparams", type_="foreignkey")
    op.drop_column("gamesparams", "apiKey_used")
    op.drop_constraint(None, "games", type_="foreignkey")
    op.drop_column("games", "apiKey_used")
    op.drop_index(op.f("ix_apikey_id"), table_name="apikey")
    op.drop_table("apikey")
    # ### end Alembic commands ###
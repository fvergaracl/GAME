"""delete apikey unused column

Revision ID: f864fafa202d
Revises: eee9ef17ced6
Create Date: 2024-11-18 12:11:33.081925

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f864fafa202d"
down_revision = "eee9ef17ced6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("apikey_apiKey_used_fkey", "apikey", type_="foreignkey")
    op.drop_column("apikey", "apiKey_used")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "apikey",
        sa.Column("apiKey_used", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "apikey_apiKey_used_fkey", "apikey", "apikey", ["apiKey_used"], ["apiKey"]
    )
    # ### end Alembic commands ###

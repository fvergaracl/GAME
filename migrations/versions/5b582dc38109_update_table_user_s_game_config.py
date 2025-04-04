"""update table user's game config

Revision ID: 5b582dc38109
Revises: e6ecec5e79c9
Create Date: 2025-02-26 12:28:24.356352

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5b582dc38109"
down_revision = "e6ecec5e79c9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "usergameconfig",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "usergameconfig",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "usergameconfig", sa.Column("apiKey_used", sa.String(), nullable=True)
    )
    op.add_column(
        "usergameconfig", sa.Column("oauth_user_id", sa.String(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("usergameconfig", "oauth_user_id")
    op.drop_column("usergameconfig", "apiKey_used")
    op.drop_column("usergameconfig", "updated_at")
    op.drop_column("usergameconfig", "created_at")
    # ### end Alembic commands ###

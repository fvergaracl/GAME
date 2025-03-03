"""ouath foreign key

Revision ID: ead50e21dd4f
Revises: 8559703645d0
Create Date: 2024-11-18 11:48:11.414667

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ead50e21dd4f"
down_revision = "8559703645d0"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("logs_apiKey_used_fkey", "logs", type_="foreignkey")
    op.drop_constraint("logs_oauth_user_id_fkey", "logs", type_="foreignkey")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(
        "logs_oauth_user_id_fkey",
        "logs",
        "oauthusers",
        ["oauth_user_id"],
        ["provider_user_id"],
    )
    op.create_foreign_key(
        "logs_apiKey_used_fkey", "logs", "apikey", ["apiKey_used"], ["apiKey"]
    )
    # ### end Alembic commands ###

"""endDateTime deleted in games

Revision ID: 9cdfc1ddb317
Revises: e4b1dfd6c2a9
Create Date: 2024-03-25 11:19:27.349861

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9cdfc1ddb317'
down_revision = 'e4b1dfd6c2a9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('games', 'endDateTime')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('games', sa.Column('endDateTime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
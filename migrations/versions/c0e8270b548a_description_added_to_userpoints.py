"""description added to UserPoints

Revision ID: c0e8270b548a
Revises: 63dd25f00eb9
Create Date: 2024-02-05 16:07:10.959924

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0e8270b548a'
down_revision = '63dd25f00eb9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('userpoints', sa.Column('description', sa.String(), nullable=True))
    op.alter_column('wallettransactions', 'coins',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('wallettransactions', 'coins',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.drop_column('userpoints', 'description')
    # ### end Alembic commands ###
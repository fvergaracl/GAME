"""status added in task

Revision ID: 7a1427d45348
Revises: 9cdfc1ddb317
Create Date: 2024-06-18 11:11:15.791568

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a1427d45348'
down_revision = '9cdfc1ddb317'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Add the column with a default value for existing rows
    op.add_column('tasks', sa.Column('status', sa.String(),
                  nullable=False, server_default='pending'))

    # Optionally, drop the server default if you don't want it to apply to new
    #  rows
    op.alter_column('tasks', 'status', server_default=None)

    op.alter_column('tasks', 'externalTaskId',
                    existing_type=sa.VARCHAR(),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tasks', 'externalTaskId',
                    existing_type=sa.VARCHAR(),
                    nullable=True)
    op.drop_column('tasks', 'status')
    # ### end Alembic commands ###

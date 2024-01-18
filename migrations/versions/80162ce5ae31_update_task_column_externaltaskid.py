"""update task column (externalTaskId)

Revision ID: 80162ce5ae31
Revises: 9745cccfeb60
Create Date: 2024-01-18 16:46:27.063030

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '80162ce5ae31'
down_revision = '9745cccfeb60'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('externalTaskId', postgresql.UUID(as_uuid=True), nullable=True))
    op.drop_constraint('tasks_externalTaskID_key', 'tasks', type_='unique')
    op.create_unique_constraint(None, 'tasks', ['externalTaskId'])
    op.drop_column('tasks', 'externalTaskID')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('externalTaskID', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'tasks', type_='unique')
    op.create_unique_constraint('tasks_externalTaskID_key', 'tasks', ['externalTaskID'])
    op.drop_column('tasks', 'externalTaskId')
    # ### end Alembic commands ###

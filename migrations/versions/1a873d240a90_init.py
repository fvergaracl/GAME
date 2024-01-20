"""init

Revision ID: 1a873d240a90
Revises: 
Create Date: 2024-01-20 12:37:56.217366

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a873d240a90'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('games',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('externalGameId', sa.String(), nullable=True),
    sa.Column('platform', sa.String(), nullable=True),
    sa.Column('endDateTime', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('externalGameId')
    )
    op.create_table('strategy',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('strategyName', sa.String(), nullable=True),
    sa.Column('data', sa.String(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('strategyName')
    )
    op.create_table('users',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('externalUserID', sa.String(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('externalUserID')
    )
    op.create_table('gameparams',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('param', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('gameId', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['gameId'], ['games.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tasks',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('externalTaskId', sa.String(), nullable=True),
    sa.Column('gameId', sa.Integer(), nullable=True),
    sa.Column('strategyId', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['gameId'], ['games.id'], ),
    sa.ForeignKeyConstraint(['strategyId'], ['strategy.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('wallet',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('coinsBalance', sa.Float(), nullable=True),
    sa.Column('pointsBalance', sa.Float(), nullable=True),
    sa.Column('conversionRate', sa.Float(), nullable=True),
    sa.Column('userId', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['userId'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('userpoints',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('points', sa.Integer(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('userId', sa.Integer(), nullable=True),
    sa.Column('taskId', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['taskId'], ['tasks.id'], ),
    sa.ForeignKeyConstraint(['userId'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('wallettransactions',
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('transactionType', sa.String(), nullable=True),
    sa.Column('points', sa.Integer(), nullable=True),
    sa.Column('appliedConversionRate', sa.Float(), nullable=True),
    sa.Column('walletId', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['walletId'], ['wallet.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('wallettransactions')
    op.drop_table('userpoints')
    op.drop_table('wallet')
    op.drop_table('tasks')
    op.drop_table('gameparams')
    op.drop_table('users')
    op.drop_table('strategy')
    op.drop_table('games')
    # ### end Alembic commands ###

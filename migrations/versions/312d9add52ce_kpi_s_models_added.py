"""KPI's models added

Revision ID: 312d9add52ce
Revises: 681958fa2dd8
Create Date: 2024-10-01 15:07:38.051491

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '312d9add52ce'
down_revision = '681958fa2dd8'
branch_labels = None
depends_on = None


def upgrade():
    # Crear la tabla kpimetrics
    op.create_table('kpimetrics',
                    sa.Column('id', postgresql.UUID(
                        as_uuid=True), nullable=False),
                    sa.Column('created_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('updated_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('apiKey_used', sa.String(), nullable=True),
                    sa.Column('day', sa.String(), nullable=True),
                    sa.Column('totalRequests', sa.Integer(), nullable=True),
                    sa.Column('successRate', sa.Integer(), nullable=True),
                    sa.Column('avgLatencyMS', sa.Integer(), nullable=True),
                    sa.Column('errorRate', sa.Integer(), nullable=True),
                    sa.Column('activeUsers', sa.Integer(), nullable=True),
                    sa.Column('retentionRate', sa.Integer(), nullable=True),
                    sa.Column('avgInteractionsPerUser',
                              sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['apiKey_used'], ['apikey.apiKey'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_kpimetrics_id'),
                    'kpimetrics', ['id'], unique=False)

    op.create_table('uptimelogs',
                    sa.Column('id', postgresql.UUID(
                        as_uuid=True), nullable=False),
                    sa.Column('created_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('updated_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('apiKey_used', sa.String(), nullable=True),
                    sa.Column('status', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['apiKey_used'], ['apikey.apiKey'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_uptimelogs_id'),
                    'uptimelogs', ['id'], unique=False)

    op.create_table('apirequests',
                    sa.Column('id', postgresql.UUID(
                        as_uuid=True), nullable=False),
                    sa.Column('created_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('updated_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('apiKey_used', sa.String(), nullable=True),
                    sa.Column('userId', postgresql.UUID(
                        as_uuid=True), nullable=True),
                    sa.Column('endpoint', sa.String(), nullable=True),
                    sa.Column('statusCode', sa.Integer(), nullable=True),
                    sa.Column('responseTimeMS', sa.Integer(), nullable=True),
                    sa.Column('requestType', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['apiKey_used'], ['apikey.apiKey'], ),
                    sa.ForeignKeyConstraint(['userId'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_apirequests_id'),
                    'apirequests', ['id'], unique=False)

    op.create_table('userinteractions',
                    sa.Column('id', postgresql.UUID(
                        as_uuid=True), nullable=False),
                    sa.Column('created_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('updated_at', sa.DateTime(
                        timezone=True), nullable=True),
                    sa.Column('apiKey_used', sa.String(), nullable=True),
                    sa.Column('userId', postgresql.UUID(
                        as_uuid=True), nullable=True),
                    sa.Column('taskId', postgresql.UUID(
                        as_uuid=True), nullable=True),
                    sa.Column('interactionType', sa.String(), nullable=True),
                    sa.Column('interactionDetail', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['apiKey_used'], ['apikey.apiKey'], ),
                    sa.ForeignKeyConstraint(['taskId'], ['tasks.id'], ),
                    sa.ForeignKeyConstraint(['userId'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_userinteractions_id'),
                    'userinteractions', ['id'], unique=False)

    generated_uuid = str(uuid.uuid4())
    op.execute(
        f"""
        INSERT INTO kpimetrics (id, created_at, updated_at, day)
        VALUES ('{generated_uuid}', NOW(), NOW(),
        TO_CHAR(NOW(), 'YYYY-MM-DD'));
        """
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_userinteractions_id'),
                  table_name='userinteractions')
    op.drop_table('userinteractions')
    op.drop_index(op.f('ix_apirequests_id'), table_name='apirequests')
    op.drop_table('apirequests')
    op.drop_index(op.f('ix_uptimelogs_id'), table_name='uptimelogs')
    op.drop_table('uptimelogs')
    op.drop_index(op.f('ix_kpimetrics_id'), table_name='kpimetrics')
    op.drop_table('kpimetrics')
    # ### end Alembic commands ###

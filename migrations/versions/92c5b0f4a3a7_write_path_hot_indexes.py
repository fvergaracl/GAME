"""write path hot indexes

Revision ID: 92c5b0f4a3a7
Revises: 6f2e4b9a1c3d
Create Date: 2026-02-12 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "92c5b0f4a3a7"
down_revision = "6f2e4b9a1c3d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_tasks_game_external_task ON tasks ("gameId", "externalTaskId")'
    )
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_useractions_user_created_at ON useractions ("userId", created_at)'
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_useractions_user_created_at")
    op.execute("DROP INDEX IF EXISTS ix_tasks_game_external_task")

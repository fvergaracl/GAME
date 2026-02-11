"""write path indexes and idempotency support

Revision ID: 6f2e4b9a1c3d
Revises: c1a7c6f9d2b0
Create Date: 2026-02-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6f2e4b9a1c3d"
down_revision = "c1a7c6f9d2b0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("userpoints", sa.Column("idempotencyKey", sa.String(), nullable=True))
    op.create_unique_constraint(
        "uq_user_points_user_task_idempotency",
        "userpoints",
        ["userId", "taskId", "idempotencyKey"],
    )
    op.create_index(
        "ix_user_points_task_user_created",
        "userpoints",
        ["taskId", "userId", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_game_external_task",
        "tasks",
        ["gameId", "externalTaskId"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_tasks_game_external_task", table_name="tasks")
    op.drop_index("ix_user_points_task_user_created", table_name="userpoints")
    op.drop_constraint(
        "uq_user_points_user_task_idempotency",
        "userpoints",
        type_="unique",
    )
    op.drop_column("userpoints", "idempotencyKey")

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.core.config import configs
from app.model.abuse_limit_counter import AbuseLimitCounter
from app.model.api_key import ApiKey
from app.model.api_requests import ApiRequests
from app.model.game_params import GamesParams
from app.model.games import Games
from app.model.kpi_metrics import KpiMetrics
from app.model.logs import Logs
from app.model.oauth_users import OAuthUsers
from app.model.task_params import TasksParams
from app.model.tasks import Tasks
from app.model.uptime_logs import UptimeLogs
from app.model.user_actions import UserActions
from app.model.user_game_config import UserGameConfig
from app.model.user_points import UserPoints
from app.model.users import Users
from app.model.wallet import Wallet
from app.model.wallet_transactions import WalletTransactions

cmd_kwargs = context.get_x_argument(as_dictionary=True)
if "ENV" in cmd_kwargs:
    os.environ["ENV"] = cmd_kwargs["ENV"]
    ENV = cmd_kwargs["ENV"]
else:
    ENV = "test"


config = context.config
db_url = os.getenv("ALEMBIC_DATABASE_URL") or configs.DATABASE_URI
if not db_url:
    raise RuntimeError(
        "No DB URL found. Set ALEMBIC_DATABASE_URL or configs.DATABASE_URI"
    )

config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = SQLModel.metadata


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    db_config = config.get_section(config.config_ini_section)
    connectable = engine_from_config(
        db_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    pass
else:
    run_migrations_online()

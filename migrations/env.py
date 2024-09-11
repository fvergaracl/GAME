import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.core.config import configs
from app.model.api_key import ApiKey
from app.model.game_params import GamesParams
from app.model.games import Games
from app.model.task_params import TasksParams
from app.model.tasks import Tasks
from app.model.user_actions import UserActions
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

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", configs.DATABASE_URI)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# code doesn't reach here
# def run_migrations_offline():
# """Run migrations in 'offline' mode.
#
# This configures the context with just a URL
# and not an Engine, though an Engine is acceptable
# here as well.  By skipping the Engine creation
# we don't even need a DBAPI to be available.
#
# Calls to context.execute() here emit the given string to the
# script output.
#
# """
# url = config.get_main_option("sqlalchemy.url")
# context.configure(
#     url=url,
#     target_metadata=target_metadata,
#     literal_binds=True,
#     include_schemas=True,
#     dialect_opts={"paramstyle": "named"},
# )
#
# with context.begin_transaction():
#     context.run_migrations()


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
    # run_migrations_offline()
else:
    run_migrations_online()

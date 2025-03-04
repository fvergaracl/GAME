import os
from sqlalchemy import engine_from_config, pool
from alembic import context

# Cargar la URL de la base de datos desde variables de entorno
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "changethis")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
GAME_DB_NAME = os.getenv("GAME_DB_NAME", "game_dev_db")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{GAME_DB_NAME}"

# Establecer la URL en la configuración de Alembic
config.set_main_option("sqlalchemy.url", DATABASE_URL)

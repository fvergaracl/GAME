from pydantic import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()


class Config(BaseSettings):
    ENV: str = os.getenv("ENV", "dev")
    DEBUG: bool = True
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = os.getenv("APP_PORT", "8001")
    WRITER_DB_URL: str = os.getenv(
        "DEV_DATABASE_URL_WRITE", "postgresql+asyncpg://root:example@db:5432/game_dev_db")
    READER_DB_URL: str = os.getenv(
        "DEV_DATABASE_URL_READ", "postgresql+asyncpg://root:example@db:5432/game_dev_db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    SENTRY_SDN: str = None
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL", "amqp://user:bitnami@localhost:5672/")
    CELERY_BACKEND_URL: str = os.getenv(
        "CELERY_BACKEND_URL", "redis://:password123@localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = 6379


class DevelopmentConfig(Config):
    WRITER_DB_URL: str = os.getenv(
        "DEV_DATABASE_URL_WRITE", "postgresql+asyncpg://root:example@localhost:5432/game_dev_db")
    READER_DB_URL: str = os.getenv(
        "DEV_DATABASE_URL_READ", "postgresql+asyncpg://root:example@localhost:5432/game_dev_db")
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


class LocalConfig(Config):
    WRITER_DB_URL: str = os.getenv(
        "LOCAL_DATABASE_URL_WRITE", "postgresql+asyncpg://root:example@db:5432/game_dev_db")
    READER_DB_URL: str = os.getenv(
        "LOCAL_DATABASE_URL_READ", "postgresql+asyncpg://root:example@db:5432/game_dev_db")


class ProductionConfig(Config):
    DEBUG: str = False
    WRITER_DB_URL: str = os.getenv(
        "PROD_DATABASE_URL_WRITE", "postgresql+asyncpg://root:example@db:5432/game_dev_db")
    READER_DB_URL: str = os.getenv(
        "PROD_DATABASE_URL_READ", "postgresql+asyncpg://root:example@db:5432/game_dev_db")


def get_config():
    env = os.getenv("ENV", "dev")
    config_type = {
        "dev": DevelopmentConfig(),
        "local": LocalConfig(),
        "prod": ProductionConfig(),
    }
    return config_type[env]


config: Config = get_config()

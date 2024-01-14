import os

from pydantic_settings import BaseSettings

class EnvConfig(BaseSettings):
    DB_DRIVER: str = os.getenv("DB_DRIVER", "postgresql+asyncpg")
    DB_NAME: str = os.getenv("DB_NAME", "fastapi")
    DB_USER: str = os.getenv("DB_USER", "fastapi")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "fastapi")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = os.getenv("DB_PORT", 5432)
    WRITER_DB_URL: str = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    READER_DB_URL: str = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class EnvTestConfig(BaseSettings):
    DB_TEST_DRIVER: str = os.getenv("DB_TEST_DRIVER", "postgresql+asyncpg")
    DB_TEST_NAME: str = os.getenv("DB_TEST_NAME", "fastapi_test")
    DB_TEST_USER: str = os.getenv("DB_TEST_USER", "fastapi")
    DB_TEST_PASSWORD: str = os.getenv("DB_TEST_PASSWORD", "fastapi")
    DB_TEST_HOST: str = os.getenv("DB_TEST_HOST", "localhost")
    DB_TEST_PORT: int = os.getenv("DB_TEST_PORT", 5432)
    WRITER_DB_URL: str = f"{DB_TEST_DRIVER}://{DB_TEST_USER}:{DB_TEST_PASSWORD}@{DB_TEST_HOST}:{DB_TEST_PORT}/{DB_TEST_NAME}"
    READER_DB_URL: str = f"{DB_TEST_DRIVER}://{DB_TEST_USER}:{DB_TEST_PASSWORD}@{DB_TEST_HOST}:{DB_TEST_PORT}/{DB_TEST_NAME}" 

class Config(EnvConfig):
    ENV: str = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    JWT_SECRET_KEY: str = "fastapi"
    JWT_ALGORITHM: str = "HS256"
    SENTRY_SDN: str = ""
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "amqp://user:bitnami@localhost:5672/")
    CELERY_BACKEND_URL: str = os.getenv("CELERY_BACKEND_URL", "redis://:password123@localhost:6379/0")
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


class TestConfig(Config,EnvTestConfig):
    ...


class LocalConfig(Config):
    ...


class ProductionConfig(Config):
    DEBUG: bool = False


def get_config():
    env = os.getenv("ENV", "local")
    config_type = {
        "test": TestConfig(),
        "local": LocalConfig(),
        "prod": ProductionConfig(),
    }
    return config_type[env]


config: Config = get_config()

import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


def _env_to_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_to_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Configs(BaseSettings):
    """
    Configuration class for loading environment variables and application
      settings.

    Attributes:
        ENV (str): The environment setting (e.g., 'dev', 'prod').
        API_V1_STR (str): The API version string.
        PROJECT_NAME (str): The name of the project.
        GAMIFICATIONENGINE_VERSION_APP (str): The version of the gamification
          engine application.
        ENV_DATABASE_MAPPER (dict): A mapping of environments to database
          names.
        DEFAULT_CONVERTION_RATE_POINTS_TO_COIN (int): The default conversion
          rate from points to coins.
        SECRET_KEY (str): The secret key for the application . Important to
          simulate points
        BACKEND_CORS_ORIGINS (List[str]): A list of allowed CORS origins.
        KEYCLOAK_REALM (str): The Keycloak realm.
        KEYCLOAK_CLIENT_ID (str): The Keycloak client ID.
        KEYCLOAK_CLIENT_SECRET (str): The Keycloak client secret.
        KEYCLOAK_URL (str): The Keycloak URL.
        KEYCLOAK_URL_DOCKER (str): The Keycloak URL for Docker.
        DB_USER (str): The database user.
        DB_PASSWORD (str): The database password.
        DB_HOST (str): The database host.
        DB_PORT (str): The database port.
        DB_ENGINE (str): The database engine.
        DATABASE_URI (str): The URI for the database connection.
        PAGE (int): The default page number for queries.
        PAGE_SIZE (int): The default page size for queries.
        ORDERING (str): The default ordering for queries.

        ABUSE_PREVENTION_ENABLED (bool): Enables abuse prevention checks for
          sensitive endpoints.
        ABUSE_RATE_LIMIT_WINDOW_SECONDS (int): Time window in seconds for
          short-window rate limiting.
        ABUSE_RATE_LIMIT_PER_API_KEY (int): Max requests allowed per API key
          inside the short window.
        ABUSE_RATE_LIMIT_PER_IP (int): Max requests allowed per source IP
          inside the short window.
        ABUSE_RATE_LIMIT_PER_EXTERNAL_USER (int): Max requests allowed per
          external user id inside the short window.
        ABUSE_DAILY_QUOTA_PER_API_KEY (int): Daily quota for sensitive
          operations per API key.
    """

    ENV: str = os.getenv("ENV", "dev")
    ROOT_PATH: str = os.getenv("ROOT_PATH", "")
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GAME-api"
    GAMIFICATIONENGINE_VERSION_APP: str = os.getenv(
        "GAMIFICATIONENGINE_VERSION_APP", "No_version"
    )

    SENTRY_DSN: str = os.getenv("SENTRY_DSN", None)
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "dev")
    SENTRY_RELEASE: str = os.getenv("SENTRY_RELEASE", "0.0.0")

    EXTRA_SERVER_URL: str = os.getenv("EXTRA_SERVER_URL", None)
    EXTRA_SERVER_DESCRIPTION: str = os.getenv("EXTRA_SERVER_DESCRIPTION", None)

    ENV_DATABASE_MAPPER: dict = {
        "prod": "game_dev_db",
        "stage": "game_dev_db",
        "dev": "game_dev_db",
        "test": "test_game_dev_db",
    }
    DEFAULT_CONVERTION_RATE_POINTS_TO_COIN: int = os.getenv(
        "DEFAULT_CONVERTION_RATE_POINTS_TO_COIN", 100
    )
    SECRET_KEY: str = str(os.getenv("SECRET_KEY", None))
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # keycloak
    KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
    KEYCLOAK_AUDIENCE = os.getenv("KEYCLOAK_AUDIENCE", "account")
    KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
    KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "admin-client-secret")
    KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    KEYCLOAK_URL_DOCKER = os.getenv("KEYCLOAK_URL_DOCKER", "http://keycloak:8080")
    # database
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_ENGINE: str = os.getenv("DB_ENGINE", "postgresql")

    DATABASE_URI = (
        "{db_engine}://{user}:{password}@{host}:{port}/{database}".format(  # noqa: E501
            db_engine=DB_ENGINE,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=ENV_DATABASE_MAPPER[ENV],
        )
    )

    # find query
    PAGE = 1
    PAGE_SIZE = 10
    ORDERING = "-id"

    ABUSE_PREVENTION_ENABLED: bool = _env_to_bool(
        "ABUSE_PREVENTION_ENABLED", True
    )
    ABUSE_RATE_LIMIT_WINDOW_SECONDS: int = _env_to_int(
        "ABUSE_RATE_LIMIT_WINDOW_SECONDS", 60
    )
    ABUSE_RATE_LIMIT_PER_API_KEY: int = _env_to_int(
        "ABUSE_RATE_LIMIT_PER_API_KEY", 120
    )
    ABUSE_RATE_LIMIT_PER_IP: int = _env_to_int("ABUSE_RATE_LIMIT_PER_IP", 240)
    ABUSE_RATE_LIMIT_PER_EXTERNAL_USER: int = _env_to_int(
        "ABUSE_RATE_LIMIT_PER_EXTERNAL_USER", 60
    )
    ABUSE_DAILY_QUOTA_PER_API_KEY: int = _env_to_int(
        "ABUSE_DAILY_QUOTA_PER_API_KEY", 10000
    )


class TestConfigs(Configs):
    """
    Test configuration class for loading test environment settings.
    Inherits from Configs.

    Attributes:
        ENV (str): The environment setting for test environment.
    """

    ENV = "test"
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
    DB_HOST = os.getenv("TEST_DB_HOST", "localhost")


configs = TestConfigs() if os.getenv("ENV") == "test" else Configs()

print("Environment:", configs.ENV)

if configs.ENV == "prod":
    print("-------------- Production Environment --------------")
elif configs.ENV == "stage":
    print("-------------- Staging Environment --------------")
elif configs.ENV == "test":
    print("-------------- Test Environment --------------")

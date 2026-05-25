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


def _parse_cors_origins(raw_value: str) -> List[str]:
    """
    Parse a comma-separated CORS origin list. Whitespace-only entries are
    dropped; an empty/whitespace-only string resolves to ``[]``.
    """
    return [
        origin.strip() for origin in raw_value.split(",") if origin.strip()
    ]


def _validate_cors_origins(env: str, origins: List[str]) -> None:
    """
    Fail fast when the API is started in a protected environment with a
    wildcard CORS allow-list -- a misconfiguration that, paired with a
    future toggle of ``allow_credentials=False``, would let any site issue
    authenticated requests on behalf of the user.
    """
    if env in {"prod", "stage"} and "*" in origins:
        raise ValueError(
            f"BACKEND_CORS_ORIGINS=['*'] is not allowed when ENV={env!r}. "
            "Set BACKEND_CORS_ORIGINS to an explicit comma-separated list "
            "of allowed origins (e.g. 'https://app.example.com,"
            "https://admin.example.com')."
        )


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

        SQLALCHEMY_ECHO (bool): Enables SQLAlchemy SQL logging.
        DB_POOL_PRE_PING (bool): Enables connection health-check before use.
        DB_POOL_SIZE (int): Persistent DB connections maintained in pool.
        DB_MAX_OVERFLOW (int): Extra connections allowed above pool size.
        DB_POOL_TIMEOUT_SECONDS (int): Seconds to wait for a free pool connection.
        DB_POOL_RECYCLE_SECONDS (int): Lifetime before recycling pooled
          connections.
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
    # CORS -- comma-separated allow-list from BACKEND_CORS_ORIGINS env var
    # (see Config.parse_env_var below). Defaults to ``[]`` (no origins) so
    # the middleware is only attached when explicit origins are configured.
    # ``"*"`` is rejected outright in ``prod``/``stage`` to avoid a misconfig
    # granting authenticated cross-site access.
    BACKEND_CORS_ORIGINS: List[str] = []

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

    SQLALCHEMY_ECHO: bool = _env_to_bool("SQLALCHEMY_ECHO", False)
    DB_POOL_PRE_PING: bool = _env_to_bool("DB_POOL_PRE_PING", True)
    DB_POOL_SIZE: int = _env_to_int("DB_POOL_SIZE", 20)
    DB_MAX_OVERFLOW: int = _env_to_int("DB_MAX_OVERFLOW", 40)
    DB_POOL_TIMEOUT_SECONDS: int = _env_to_int("DB_POOL_TIMEOUT_SECONDS", 30)
    DB_POOL_RECYCLE_SECONDS: int = _env_to_int("DB_POOL_RECYCLE_SECONDS", 1800)
    API_KEY_HEADER_CACHE_TTL_SECONDS: int = _env_to_int(
        "API_KEY_HEADER_CACHE_TTL_SECONDS", 5
    )

    class Config:
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            # Treat BACKEND_CORS_ORIGINS as a plain comma-separated list
            # instead of JSON, so operators can write
            # ``BACKEND_CORS_ORIGINS=https://a.example,https://b.example``.
            if field_name == "BACKEND_CORS_ORIGINS":
                return _parse_cors_origins(raw_val)
            return cls.json_loads(raw_val)


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

_validate_cors_origins(configs.ENV, configs.BACKEND_CORS_ORIGINS)

print("Environment:", configs.ENV)

if configs.ENV == "prod":
    print("-------------- Production Environment --------------")
elif configs.ENV == "stage":
    print("-------------- Staging Environment --------------")
elif configs.ENV == "test":
    print("-------------- Test Environment --------------")

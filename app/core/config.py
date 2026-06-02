import ipaddress
import logging
import os
from ipaddress import IPv4Network, IPv6Network
from typing import List, Optional, Union

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode
from typing_extensions import Annotated

load_dotenv()

# Bootstrap handler so module-import-time log records have somewhere to go
# before dictConfig in app.main runs. No-op on subsequent imports; dictConfig
# later replaces root handlers with disable_existing_loggers=False.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


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


def _parse_trusted_proxy_ips(
    raw_value: str,
) -> List[Union[IPv4Network, IPv6Network]]:
    """
    Parse a comma-separated list of IPs and/or CIDR ranges into
    ``ipaddress.ip_network`` objects. Bare IPs (e.g. ``10.0.0.5``) are
    coerced to /32 (IPv4) or /128 (IPv6) networks. Whitespace-only
    entries are dropped. Raises ``ValueError`` on any malformed entry so
    the misconfiguration is caught at startup rather than silently
    trusting no one in production.
    """
    networks: List[Union[IPv4Network, IPv6Network]] = []
    for entry in raw_value.split(","):
        token = entry.strip()
        if not token:
            continue
        try:
            networks.append(ipaddress.ip_network(token, strict=False))
        except ValueError as exc:
            raise ValueError(
                f"TRUSTED_PROXY_IPS entry {token!r} is not a valid IP or "
                f"CIDR range: {exc}"
            ) from exc
    return networks


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


_NON_PROD_DB_NAME_DEFAULTS = {
    "dev": "game_dev_db",
    "test": "test_game_dev_db",
}

# Convenience default for local/dev Keycloak realms. It is explicitly
# rejected in prod/stage by ``_validate_required_secrets`` so the placeholder
# can never reach a protected deployment.
_INSECURE_KEYCLOAK_CLIENT_SECRET_DEFAULT = "admin-client-secret"


def _resolve_db_name(env: str, db_name: Optional[str]) -> str:
    """
    Resolve the database name from ``DB_NAME``. Required in protected
    environments (``prod``/``stage``) so the app cannot silently fall back
    to a development database when ``DB_HOST`` is repointed.
    """
    if db_name:
        return db_name
    if env in {"prod", "stage"}:
        raise ValueError(
            f"DB_NAME must be set when ENV={env!r}. The previous "
            "ENV_DATABASE_MAPPER default ('game_dev_db') was removed to "
            "prevent prod/stage workloads from being written to a "
            "database literally named 'dev' when DB_HOST points elsewhere."
        )
    return _NON_PROD_DB_NAME_DEFAULTS.get(env, "game_dev_db")


def _validate_required_secrets(
    env: str, secret_key: str, keycloak_client_secret: str
) -> None:
    """
    Fail fast in protected environments (``prod``/``stage``) when
    security-critical secrets are missing or left at their insecure
    development defaults. Previously ``SECRET_KEY`` fell back to the literal
    string ``"None"`` -- truthy, so the ``if not configs.SECRET_KEY`` guard in
    the simulation endpoint never fired and the app signed payloads with the
    word "None"; and ``KEYCLOAK_CLIENT_SECRET`` shipped a known placeholder.
    Both now boot-block before serving a single request when misconfigured.
    """
    if env not in {"prod", "stage"}:
        return
    missing: List[str] = []
    if not secret_key:
        missing.append("SECRET_KEY")
    if (
        not keycloak_client_secret
        or keycloak_client_secret == _INSECURE_KEYCLOAK_CLIENT_SECRET_DEFAULT
    ):
        missing.append("KEYCLOAK_CLIENT_SECRET")
    if missing:
        raise ValueError(
            "The following secrets must be set to non-default values when "
            f"ENV={env!r}: {', '.join(missing)}. Configure them via the "
            "environment (never commit real secrets)."
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
        DB_NAME (Optional[str]): The database name. Required when
          ``ENV`` is ``prod`` or ``stage``; defaults to ``game_dev_db``
          (or ``test_game_dev_db`` in tests) otherwise.
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
    # Sprint 11 follow-up: when True the FastAPI app exposes /metrics via
    # prometheus_fastapi_instrumentator so the bundled docker-compose
    # Prometheus container can scrape the DSL counters out of the box.
    # Default ON because the metrics stack ships pre-configured; flip to
    # false in production deployments that front the api with an ingress
    # already blocking /metrics externally.
    METRICS_ENABLED: bool = _env_to_bool("METRICS_ENABLED", True)
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GAME-api"
    GAMIFICATIONENGINE_VERSION_APP: str = os.getenv(
        "GAMIFICATIONENGINE_VERSION_APP", "No_version"
    )

    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "dev")
    SENTRY_RELEASE: str = os.getenv("SENTRY_RELEASE", "0.0.0")

    EXTRA_SERVER_URL: Optional[str] = os.getenv("EXTRA_SERVER_URL", None)
    EXTRA_SERVER_DESCRIPTION: Optional[str] = os.getenv(
        "EXTRA_SERVER_DESCRIPTION", None
    )

    DB_NAME: Optional[str] = os.getenv("DB_NAME")
    DEFAULT_CONVERTION_RATE_POINTS_TO_COIN: int = os.getenv(
        "DEFAULT_CONVERTION_RATE_POINTS_TO_COIN", 100
    )
    # Resolve to an empty string (falsy) when unset rather than the literal
    # string "None": the simulation endpoint guards on ``if not SECRET_KEY``
    # and prod/stage boot is blocked by ``_validate_required_secrets`` below.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    # CORS -- comma-separated allow-list from BACKEND_CORS_ORIGINS env var
    # (see Config.parse_env_var below). Defaults to ``[]`` (no origins) so
    # the middleware is only attached when explicit origins are configured.
    # ``"*"`` is rejected outright in ``prod``/``stage`` to avoid a misconfig
    # granting authenticated cross-site access.
    BACKEND_CORS_ORIGINS: Annotated[List[str], NoDecode] = []

    # Comma-separated list of IPs / CIDR ranges allowed to set forwarding
    # headers (X-Forwarded-For, X-Real-IP). Empty (default) means NO proxy
    # is trusted -- forwarding headers are ignored and the socket peer is
    # used as the client IP. This is the secure default; populate with the
    # IP of the reverse proxy / ingress when running behind Traefik /
    # nginx / ALB. See H10 -- without this gate, any client can forge
    # X-Forwarded-For to bypass per-IP abuse limits.
    TRUSTED_PROXY_IPS: Annotated[
        List[Union[IPv4Network, IPv6Network]], NoDecode
    ] = []

    # keycloak
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "master")
    KEYCLOAK_AUDIENCE: str = os.getenv("KEYCLOAK_AUDIENCE", "account")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv(
        "KEYCLOAK_CLIENT_SECRET", _INSECURE_KEYCLOAK_CLIENT_SECRET_DEFAULT
    )
    KEYCLOAK_URL: str = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    KEYCLOAK_URL_DOCKER: str = os.getenv(
        "KEYCLOAK_URL_DOCKER", "http://keycloak:8080"
    )
    # database
    DB_USER: Optional[str] = os.getenv("DB_USER")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    DB_HOST: Optional[str] = os.getenv("DB_HOST")
    # Default to the PostgreSQL port (5432) to match DB_ENGINE; the previous
    # 3306 default was MySQL's and silently mismatched the engine.
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_ENGINE: str = os.getenv("DB_ENGINE", "postgresql")

    DATABASE_URI: str = (
        "{db_engine}://{user}:{password}@{host}:{port}/{database}".format(  # noqa: E501
            db_engine=DB_ENGINE,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database=_resolve_db_name(ENV, DB_NAME),
        )
    )

    # find query
    PAGE: int = 1
    PAGE_SIZE: int = 10
    ORDERING: str = "-id"

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
    # "database" keeps the original abuse_limit_counter writes; "redis" uses
    # INCR + EXPIRE against REDIS_URL (atomic, ~50 us vs ~5 ms for the UPDATE
    # on a hot Postgres row, and naturally distributed across instances).
    ABUSE_PREVENTION_BACKEND: str = os.getenv(
        "ABUSE_PREVENTION_BACKEND", "database"
    )
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    RATE_LIMIT_REDIS_KEY_PREFIX: str = os.getenv(
        "RATE_LIMIT_REDIS_KEY_PREFIX", "game:rl:"
    )
    RATE_LIMIT_TTL_BUFFER_SECONDS: int = _env_to_int(
        "RATE_LIMIT_TTL_BUFFER_SECONDS", 5
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
    # "memory" keeps the original per-process dict (one cache per gunicorn
    # worker -- revocations only land on the worker that handled the
    # request); "redis" shares the cache across workers via REDIS_URL so
    # revocations propagate on the next request.
    APIKEY_CACHE_BACKEND: str = os.getenv("APIKEY_CACHE_BACKEND", "memory")
    APIKEY_CACHE_REDIS_KEY_PREFIX: str = os.getenv(
        "APIKEY_CACHE_REDIS_KEY_PREFIX", "game:apikey:"
    )

    # DSL interpreter limits (Sprint 4). The validator rejects ASTs whose
    # static node count or depth exceeds these thresholds, so runtime should
    # never hit them — they are belt-and-braces guards in case future changes
    # introduce dynamic expansion. The wall-clock timeout is the backstop
    # against a CPU-bound walk; the interpreter yields cooperatively every
    # ~64 nodes so asyncio.wait_for can actually cancel it.
    DSL_EXECUTION_TIMEOUT_MS: int = _env_to_int("DSL_EXECUTION_TIMEOUT_MS", 500)
    DSL_MAX_NODES: int = _env_to_int("DSL_MAX_NODES", 1000)
    DSL_MAX_DEPTH: int = _env_to_int("DSL_MAX_DEPTH", 32)

    # Sprint 11: sampled persistence of DSL execution traces. Errors are
    # always persisted regardless of the sample rate -- the rate only
    # applies to OK runs. 0.0 disables successful-run sampling; 1.0
    # persists every run (only safe in dev/test, see runbook).
    DSL_EXECUTION_LOG_ENABLED: bool = _env_to_bool(
        "DSL_EXECUTION_LOG_ENABLED", True
    )
    DSL_EXECUTION_LOG_SAMPLE_RATE: float = float(
        os.getenv("DSL_EXECUTION_LOG_SAMPLE_RATE", "0.05")
    )
    # Bound the persisted trace length per row so a worst-case 1000-node
    # AST doesn't store a 1000-entry array in JSONB on every sample.
    # When truncated we drop tail entries (the early ones are usually
    # the discriminating ones for "why did this rule match").
    DSL_EXECUTION_LOG_TRACE_LIMIT: int = _env_to_int(
        "DSL_EXECUTION_LOG_TRACE_LIMIT", 200
    )

    # Sprint 13: the execution-log DB write is drained off the scoring
    # hot-path by a background worker fed from a bounded in-process queue
    # (see DslExecutionObserver). This caps how many pending rows the
    # queue holds before it starts dropping (and counting via
    # dsl_execution_log_dropped_total) rather than applying backpressure
    # to scoring. Sized for a burst: at the default 5% sample rate this is
    # ~minutes of buffer for a busy realm while the DB catches up.
    DSL_EXECUTION_LOG_QUEUE_MAXSIZE: int = _env_to_int(
        "DSL_EXECUTION_LOG_QUEUE_MAXSIZE", 1000
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _coerce_cors_origins(
        cls, value: Union[str, List[str], None]
    ) -> List[str]:
        # Treat BACKEND_CORS_ORIGINS as a plain comma-separated list instead
        # of JSON, so operators can write
        # ``BACKEND_CORS_ORIGINS=https://a.example,https://b.example``.
        if value is None:
            return []
        if isinstance(value, str):
            return _parse_cors_origins(value)
        return value

    @field_validator("TRUSTED_PROXY_IPS", mode="before")
    @classmethod
    def _coerce_trusted_proxy_ips(
        cls, value: Union[str, List, None]
    ) -> List[Union[IPv4Network, IPv6Network]]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return _parse_trusted_proxy_ips(value)
        return list(value)


class TestConfigs(Configs):
    """
    Test configuration class for loading test environment settings.
    Inherits from Configs.

    Attributes:
        ENV (str): The environment setting for test environment.
    """

    ENV: str = "test"
    DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
    DB_HOST: Optional[str] = os.getenv("TEST_DB_HOST", "localhost")


configs = TestConfigs() if os.getenv("ENV") == "test" else Configs()

_validate_cors_origins(configs.ENV, configs.BACKEND_CORS_ORIGINS)
_validate_required_secrets(
    configs.ENV, configs.SECRET_KEY, configs.KEYCLOAK_CLIENT_SECRET
)

logger.info("Environment: %s", configs.ENV)

if configs.ENV == "prod":
    logger.info("-------------- Production Environment --------------")
elif configs.ENV == "stage":
    logger.info("-------------- Staging Environment --------------")
elif configs.ENV == "test":
    logger.info("-------------- Test Environment --------------")

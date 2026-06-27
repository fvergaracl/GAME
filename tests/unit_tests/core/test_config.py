import importlib
import logging
import os

import pytest

import app.core.config as config_module


@pytest.fixture(autouse=True)
def restore_config_module():
    saved = {
        key: os.getenv(key)
        for key in (
            "ENV",
            "BACKEND_CORS_ORIGINS",
            "DB_NAME",
            "DB_PORT",
            "SECRET_KEY",
            "KEYCLOAK_CLIENT_SECRET",
        )
    }
    yield
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    importlib.reload(config_module)


def _neutralize_dotenv(monkeypatch):
    """
    Stop ``load_dotenv()`` from repopulating env vars off a developer's local
    ``.env`` when the module body re-runs on reload, so each test asserts the
    behaviour of the *environment it sets*, not the checkout's .env. Patching
    the module attribute would not survive reload (which re-executes
    ``from dotenv import load_dotenv``), so patch it at the source.
    """
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)


@pytest.mark.parametrize(
    "env_value,expected_banner",
    [
        ("prod", "-------------- Production Environment --------------"),
        ("stage", "-------------- Staging Environment --------------"),
        ("test", "-------------- Test Environment --------------"),
    ],
)
def test_config_prints_banner_for_environment(
    env_value, expected_banner, monkeypatch, caplog
):
    monkeypatch.setenv("ENV", env_value)
    if env_value in {"prod", "stage"}:
        # Protected envs now boot-block without DB_NAME and without real
        # secrets (see _validate_required_secrets); supply them so this test
        # is self-contained and does not depend on a local .env (which is
        # gitignored and absent in CI).
        monkeypatch.setenv("DB_NAME", "game_test_db")
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("KEYCLOAK_CLIENT_SECRET", "test-kc-secret")

    with caplog.at_level(logging.INFO, logger="app.core.config"):
        reloaded = importlib.reload(config_module)

    assert f"Environment: {reloaded.configs.ENV}" in caplog.text
    assert expected_banner in caplog.text


def test_cors_origins_default_to_empty_when_env_unset(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("BACKEND_CORS_ORIGINS", raising=False)
    # Neutralize load_dotenv at its source so a developer's local .env (which
    # ships BACKEND_CORS_ORIGINS=http://localhost:3000) cannot repopulate the
    # var when the module body re-runs ``load_dotenv()`` on reload and mask the
    # secure default. Patching the module attribute would not survive reload,
    # which re-executes ``from dotenv import load_dotenv``. This asserts the
    # true M3 guarantee: with nothing configured, the allow-list is empty.
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.BACKEND_CORS_ORIGINS == []


def test_cors_origins_parse_comma_separated_env_value(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        "https://app.example.com, https://admin.example.com ,",
    )

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.BACKEND_CORS_ORIGINS == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


@pytest.mark.parametrize("env_value", ["prod", "stage"])
def test_cors_origins_wildcard_rejected_in_protected_envs(env_value, monkeypatch):
    monkeypatch.setenv("ENV", env_value)
    monkeypatch.setenv("DB_NAME", "game_test_db")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "*")

    with pytest.raises(ValueError, match="BACKEND_CORS_ORIGINS"):
        importlib.reload(config_module)


def test_cors_origins_wildcard_allowed_in_dev(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "*")

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.BACKEND_CORS_ORIGINS == ["*"]


def test_secret_key_defaults_to_empty_string_when_unset(monkeypatch):
    # Q4: previously str(os.getenv("SECRET_KEY", None)) -> the literal "None"
    # (truthy), so `if not configs.SECRET_KEY` never fired. It must resolve to
    # a falsy empty string when nothing is configured.
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    _neutralize_dotenv(monkeypatch)

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.SECRET_KEY == ""


def test_db_port_defaults_to_postgres_port(monkeypatch):
    # Q5: the old default was 3306 (MySQL) despite DB_ENGINE=postgresql.
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("DB_PORT", raising=False)
    _neutralize_dotenv(monkeypatch)

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.DB_PORT == "5432"


def test_missing_secret_key_rejected_in_protected_envs(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DB_NAME", "game_test_db")
    monkeypatch.setenv("KEYCLOAK_CLIENT_SECRET", "real-kc-secret")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    _neutralize_dotenv(monkeypatch)

    with pytest.raises(ValueError, match="SECRET_KEY"):
        importlib.reload(config_module)


def test_placeholder_keycloak_secret_rejected_in_protected_envs(monkeypatch):
    monkeypatch.setenv("ENV", "stage")
    monkeypatch.setenv("DB_NAME", "game_test_db")
    monkeypatch.setenv("SECRET_KEY", "real-secret")
    # The shipped dev convenience default must never reach prod/stage.
    monkeypatch.setenv("KEYCLOAK_CLIENT_SECRET", "admin-client-secret")
    _neutralize_dotenv(monkeypatch)

    with pytest.raises(ValueError, match="KEYCLOAK_CLIENT_SECRET"):
        importlib.reload(config_module)


def test_secrets_not_required_outside_protected_envs(monkeypatch):
    # Dev/test must still boot with no secrets configured.
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("KEYCLOAK_CLIENT_SECRET", raising=False)
    _neutralize_dotenv(monkeypatch)

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.ENV == "dev"
    assert reloaded.configs.SECRET_KEY == ""


def test_sentry_defaults_are_privacy_conservative_in_prod(monkeypatch):
    # With ENV=prod and no Sentry overrides the app must not ship PII to
    # Sentry, must sample performance traces below 1.0, and must leave the
    # continuous profiler off. These feed sentry_sdk.init in app.main.
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DB_NAME", "game_test_db")
    monkeypatch.setenv("SECRET_KEY", "real-secret")
    monkeypatch.setenv("KEYCLOAK_CLIENT_SECRET", "real-kc-secret")
    for key in (
        "SENTRY_SEND_DEFAULT_PII",
        "SENTRY_TRACES_SAMPLE_RATE",
        "SENTRY_PROFILING_ENABLED",
    ):
        monkeypatch.delenv(key, raising=False)
    _neutralize_dotenv(monkeypatch)

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.SENTRY_SEND_DEFAULT_PII is False
    assert reloaded.configs.SENTRY_TRACES_SAMPLE_RATE < 1.0
    assert reloaded.configs.SENTRY_TRACES_SAMPLE_RATE == 0.1
    assert reloaded.configs.SENTRY_PROFILING_ENABLED is False


def test_sentry_settings_honour_env_overrides(monkeypatch):
    # Operators can opt back into richer (costlier/PII-bearing) collection per
    # environment without code changes.
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("SENTRY_SEND_DEFAULT_PII", "true")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")
    monkeypatch.setenv("SENTRY_PROFILING_ENABLED", "yes")
    _neutralize_dotenv(monkeypatch)

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.SENTRY_SEND_DEFAULT_PII is True
    assert reloaded.configs.SENTRY_TRACES_SAMPLE_RATE == 1.0
    assert reloaded.configs.SENTRY_PROFILING_ENABLED is True

import importlib
import logging
import os

import pytest

import app.core.config as config_module


@pytest.fixture(autouse=True)
def restore_config_module():
    original_env = os.getenv("ENV")
    original_cors = os.getenv("BACKEND_CORS_ORIGINS")
    original_db_name = os.getenv("DB_NAME")
    yield
    if original_env is None:
        os.environ.pop("ENV", None)
    else:
        os.environ["ENV"] = original_env
    if original_cors is None:
        os.environ.pop("BACKEND_CORS_ORIGINS", None)
    else:
        os.environ["BACKEND_CORS_ORIGINS"] = original_cors
    if original_db_name is None:
        os.environ.pop("DB_NAME", None)
    else:
        os.environ["DB_NAME"] = original_db_name
    importlib.reload(config_module)


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
        monkeypatch.setenv("DB_NAME", "game_test_db")

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

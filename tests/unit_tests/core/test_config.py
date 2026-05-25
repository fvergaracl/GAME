import importlib
import os
from unittest.mock import patch

import pytest

import app.core.config as config_module


@pytest.fixture(autouse=True)
def restore_config_module():
    original_env = os.getenv("ENV")
    original_cors = os.getenv("BACKEND_CORS_ORIGINS")
    yield
    if original_env is None:
        os.environ.pop("ENV", None)
    else:
        os.environ["ENV"] = original_env
    if original_cors is None:
        os.environ.pop("BACKEND_CORS_ORIGINS", None)
    else:
        os.environ["BACKEND_CORS_ORIGINS"] = original_cors
    importlib.reload(config_module)


@pytest.mark.parametrize(
    "env_value,expected_banner",
    [
        ("prod", "-------------- Production Environment --------------"),
        ("stage", "-------------- Staging Environment --------------"),
        ("test", "-------------- Test Environment --------------"),
    ],
)
def test_config_prints_banner_for_environment(env_value, expected_banner, monkeypatch):
    monkeypatch.setenv("ENV", env_value)

    with patch("builtins.print") as mock_print:
        reloaded = importlib.reload(config_module)

    mock_print.assert_any_call("Environment:", reloaded.configs.ENV)
    mock_print.assert_any_call(expected_banner)


def test_cors_origins_default_to_empty_when_env_unset(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.delenv("BACKEND_CORS_ORIGINS", raising=False)

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
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "*")

    with pytest.raises(ValueError, match="BACKEND_CORS_ORIGINS"):
        importlib.reload(config_module)


def test_cors_origins_wildcard_allowed_in_dev(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "*")

    reloaded = importlib.reload(config_module)

    assert reloaded.configs.BACKEND_CORS_ORIGINS == ["*"]

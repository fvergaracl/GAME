import importlib
import os
from unittest.mock import patch

import pytest

import app.core.config as config_module


@pytest.fixture(autouse=True)
def restore_config_module():
    original_env = os.getenv("ENV")
    yield
    if original_env is None:
        os.environ.pop("ENV", None)
    else:
        os.environ["ENV"] = original_env
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

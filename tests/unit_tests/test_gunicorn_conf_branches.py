import importlib
import os
from unittest.mock import patch


def _reload_gunicorn_conf():
    import app.gunicorn_conf as gunicorn_conf

    return importlib.reload(gunicorn_conf)


@patch("multiprocessing.cpu_count", return_value=4)
def test_gunicorn_uses_bind_env_when_present(_mock_cpu_count):
    with patch.dict(
        os.environ,
        {
            "WORKERS_PER_CORE": "1",
            "WEB_CONCURRENCY": "2",
            "BIND": "unix:/tmp/gunicorn.sock",
        },
        clear=True,
    ):
        gunicorn_conf = _reload_gunicorn_conf()

    assert gunicorn_conf.bind == "unix:/tmp/gunicorn.sock"


@patch("multiprocessing.cpu_count", return_value=4)
def test_gunicorn_default_concurrency_respects_max_workers(_mock_cpu_count):
    with patch.dict(
        os.environ,
        {
            "WORKERS_PER_CORE": "1",
            "MAX_WORKERS": "3",
        },
        clear=True,
    ):
        gunicorn_conf = _reload_gunicorn_conf()

    assert gunicorn_conf.workers == 3

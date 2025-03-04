import os
import unittest
from unittest.mock import patch


class TestGunicornConfig(unittest.TestCase):
    @patch("multiprocessing.cpu_count", return_value=4)
    @patch.dict(
        os.environ,
        {
            "WORKERS_PER_CORE": "1",
            "MAX_WORKERS": "8",
            "WEB_CONCURRENCY": "4",
            "HOST": "127.0.0.1",
            "PORT": "8080",
            "LOG_LEVEL": "debug",
            "ACCESS_LOG": "/var/log/access.log",
            "ERROR_LOG": "/var/log/error.log",
            "GRACEFUL_TIMEOUT": "90",
            "TIMEOUT": "100",
            "KEEP_ALIVE": "10",
        },
    )
    def test_gunicorn_config(self, mock_cpu_count):
        import app.gunicorn_conf as gunicorn_conf

        expected_log_data = {
            "loglevel": "debug",
            "workers": 4,
            "bind": "127.0.0.1:8080",
            "graceful_timeout": 90,
            "timeout": 100,
            "keepalive": 10,
            "errorlog": "/var/log/error.log",
            "accesslog": "/var/log/access.log",
            "workers_per_core": 1.0,
            "use_max_workers": 8,
            "host": "127.0.0.1",
            "port": "8080",
        }

        log_data = gunicorn_conf.log_data
        self.assertEqual(log_data, expected_log_data)


if __name__ == "__main__":
    unittest.main()

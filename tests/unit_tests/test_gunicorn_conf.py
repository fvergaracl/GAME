import unittest
import os
from unittest.mock import patch


class TestGunicornConfig(unittest.TestCase):
    # Simulamos que hay 4 núcleos
    @patch('multiprocessing.cpu_count', return_value=4)
    @patch.dict(os.environ, {
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
        "KEEP_ALIVE": "10"
    })
    def test_gunicorn_config(self, mock_cpu_count):
        # Importamos el archivo que contiene la configuración
        import app.gunicorn_conf as gunicorn_conf

        # Verificamos que las variables se configuraron correctamente
        expected_log_data = {
            "loglevel": "debug",
            "workers": 4,  # WEB_CONCURRENCY está configurado en 4
            "bind": "127.0.0.1:8080",
            "graceful_timeout": 90,
            "timeout": 100,
            "keepalive": 10,
            "errorlog": "/var/log/error.log",
            "accesslog": "/var/log/access.log",
            "workers_per_core": 1.0,  # WORKERS_PER_CORE está configurado en 1
            "use_max_workers": 8,  # MAX_WORKERS está configurado en 8
            "host": "127.0.0.1",
            "port": "8080",
        }

        # Simulamos la impresión del log_data generado en el código
        log_data = gunicorn_conf.log_data
        self.assertEqual(log_data, expected_log_data)


if __name__ == "__main__":
    unittest.main()

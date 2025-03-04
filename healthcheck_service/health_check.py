import os
import time
import uuid
from datetime import datetime

import psycopg2
import requests

DB_ENGINE = os.getenv("DB_ENGINE", "postgresql")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "postgres")
API_URL_KPI = os.getenv("API_URL_KPI", "http://localhost:8000/api/v1/kpi")


conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)


def check_if_table_exists():
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'uptimelogs'
            )
        """
        )
        return cur.fetchone()[0]


def check_api_health():
    try:
        response = requests.get(f"{API_URL_KPI}/health_check")
        if response.status_code == 200:
            return "healthy"
        else:
            return "unhealthy"
    except requests.exceptions.RequestException:
        return "unhealthy"


def save_health_check(status):
    unique_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO uptimelogs (id, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
        """,
            (unique_id, status, created_at, created_at),
        )
        conn.commit()


if __name__ == "__main__":
    print("\033[95m [i]Starting health check service\033[0m")
    table_exist = check_if_table_exists()
    while not table_exist:
        table_exist = check_if_table_exists()
        print("\033[91m [x]Table does not exist\033[0m")
        exit(1)
    while True:
        status = check_api_health()
        save_health_check(status)
        print(f"\033[92m [✔]Health check saved with status {status}\033[0m")
        time.sleep(60)

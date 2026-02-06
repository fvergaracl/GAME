#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-game_dev_db}"
DB_USER="${DB_USER:-root}"

DATABASE_URL="${DATABASE_URL:-postgresql://${DB_USER}:${DB_PASSWORD:-example}@${DB_HOST}:${DB_PORT}/${DB_NAME}}"
export DATABASE_URL

APP_DIR="${APP_DIR:-/app}"

echo "-----------------------------------------------------"
echo "DB wait: ${DB_HOST}:${DB_PORT} db=${DB_NAME} user=${DB_USER}"
echo "DATABASE_URL=${DATABASE_URL}"
echo "-----------------------------------------------------"


echo "Waiting for PostgreSQL to become available..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is up."


echo "Running Alembic migrations..."
cd "${APP_DIR}"

if command -v poetry >/dev/null 2>&1; then
  poetry run alembic upgrade head
else
  alembic upgrade head
fi
echo "Migrations done."


HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo "-----------------------------------------------------"
echo "Starting FastAPI with gunicorn (uvicorn workers)"
echo "host=${HOST} port=${PORT} log_level=${LOG_LEVEL}"
echo "-----------------------------------------------------"

exec gunicorn \
  -k "uvicorn.workers.UvicornWorker" \
  -c "app/gunicorn_conf.py" \
  "app.main:app"

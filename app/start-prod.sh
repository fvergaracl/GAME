#!/bin/bash

# Wait for PostgreSQL to become available
echo "Waiting for PostgreSQL to become available..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 1
done

echo "PostgreSQL is up - executing Alembic migrations"
# Navigate to your project directory (where pyproject.toml is located)
cd /app
# Use poetry to run Alembic migrations
poetry run alembic upgrade head


HOST=${HOST:-0.0.0.0}
PORT=${PORT}
LOG_LEVEL=${LOG_LEVEL:-info}

echo "-----------------------------------------------------"
echo "Starting in production mode with uvicorn --reload..."
echo "-----------------------------------------------------"

# Start Fastapi app
exec gunicorn -k "uvicorn.workers.UvicornWorker" -c "app/gunicorn_conf.py" "app.main:app" --reload 
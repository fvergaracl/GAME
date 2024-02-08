#!/bin/bash

# Wait for PostgreSQL to become available
echo "Waiting for PostgreSQL to become available..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 1
done

echo "PostgreSQL is up - executing Alembic migrations"
# Navigate to your project directory (where pyproject.toml is located)
cd /app/app
# Use poetry to run Alembic migrations
poetry run alembic upgrade head

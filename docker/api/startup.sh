#!/bin/bash
dockerize -wait tcp://postgres:5432 -timeout 20s

if [ "$ENV" = "dev" ]; then
    echo "Starting in development mode with uvicorn --reload..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Starting in production mode with gunicorn..."
    alembic upgrade head && gunicorn --bind 0.0.0.0:8000 -w 4 -k uvicorn.workers.UvicornWorker app.main:app
fi
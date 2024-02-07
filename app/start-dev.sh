#! /usr/bin/env bash
# https://raw.githubusercontent.com/tiangolo/uvicorn-gunicorn-docker/master/docker-images/gunicorn_conf.py

HOST=${HOST:-0.0.0.0}
PORT=${PORT}
LOG_LEVEL=${LOG_LEVEL:-info}

# Let the DB start
python /app/app/pre_start.py

# Execute only-dev stuff
python /app/app/development.py

# Changes in database are managed by alembic. CHECK MAKEFILE make migrations message="message"

# Start Uvicorn with live reload
exec uvicorn --reload --host $HOST --port $PORT --log-level $LOG_LEVEL "app.main:app"
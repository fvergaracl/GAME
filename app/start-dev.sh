#! /usr/bin/env bash
# https://raw.githubusercontent.com/tiangolo/uvicorn-gunicorn-docker/master/docker-images/gunicorn_conf.py

HOST=${HOST:-0.0.0.0}
PORT=${PORT}
LOG_LEVEL=${LOG_LEVEL:-info}



# Changes in database are managed by alembic. CHECK MAKEFILE make migrations message="message"

# Start Uvicorn with live reload
echo "-----------------------------------------------------"
echo "Starting in development mode with uvicorn --reload..."
echo "-----------------------------------------------------"
exec uvicorn --reload --host $HOST --port $PORT --log-level $LOG_LEVEL "app.main:app"
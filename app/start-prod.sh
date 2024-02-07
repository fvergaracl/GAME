#! /usr/bin/env bash
# https://raw.githubusercontent.com/tiangolo/uvicorn-gunicorn-docker/master/docker-images/gunicorn_conf.py

HOST=${HOST:-0.0.0.0}
PORT=${PORT}
LOG_LEVEL=${LOG_LEVEL:-info}


# Start Fastapi app
exec gunicorn -k "uvicorn.workers.UvicornWorker" -c "app/gunicorn_conf.py" "app.main:app"
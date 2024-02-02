#!/bin/bash
dockerize -wait tcp://postgres:5432 -timeout 20s
alembic upgrade head && gunicorn --bind 0.0.0.0:8000 -w 4 -k uvicorn.workers.UvicornWorker app.main:app
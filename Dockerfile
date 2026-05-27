# syntax=docker/dockerfile:1.7

# ---------- builder ----------
FROM python:3.11.10-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root --no-cache


# ---------- dev ----------
FROM builder AS dev

RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN poetry install --no-root --no-cache

COPY ./alembic.ini ./
COPY ./app ./app
COPY ./migrations ./migrations

RUN chmod +x ./app/start-dev.sh ./app/start-prod.sh

ENV PYTHONPATH=/app/app

EXPOSE 8000
CMD ["bash", "./app/start-dev.sh"]


# ---------- prod ----------
FROM python:3.11.10-slim AS prod

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app/app

RUN apt-get update && apt-get install -y --no-install-recommends \
        graphviz \
        postgresql-client \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app --no-create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:app /app/.venv /app/.venv

COPY --chown=appuser:app ./alembic.ini ./
COPY --chown=appuser:app ./app ./app
COPY --chown=appuser:app ./migrations ./migrations

RUN chmod +x ./app/start-prod.sh ./app/start-dev.sh \
    && install -d -o appuser -g app /app/logs

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/kpi/health_check || exit 1

CMD ["bash", "./app/start-prod.sh"]

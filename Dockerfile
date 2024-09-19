FROM python:3.11.10-slim as builder
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    build-essential \ 
    libgraphviz-dev \  
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install poetry==1.8.3
RUN poetry config virtualenvs.create false
WORKDIR /app/

COPY ./pyproject.toml ./poetry.lock* ./alembic.ini /app/
COPY ./app /app/app
COPY ./migrations /app/migrations
RUN chmod +x /app/app/start-dev.sh
RUN chmod +x /app/app/start-prod.sh
ENV PYTHONPATH=/app/app

FROM builder as dev
RUN poetry install --no-root
CMD ["bash", "./start-dev.sh"]

FROM builder as prod
RUN poetry install --no-root --no-dev --no-cache
RUN pip install gunicorn

CMD ["bash", "./app/start-prod.sh"]

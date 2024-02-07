FROM python:3.10.13-slim as builder
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN apt-get update
RUN pip3 install poetry==1.7.1
RUN poetry config virtualenvs.create false
WORKDIR /app/
# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/
COPY ./app /app/app
RUN chmod +x /app/app/start-dev.sh
RUN chmod +x /app/app/start-prod.sh
ENV PYTHONPATH=/app/app

FROM builder as dev
RUN poetry install --no-root
# FOR DATABASE DIAGRAM GENERATION
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
CMD ["bash", "./start-dev.sh"]

FROM builder as prod
RUN poetry install --no-root --no-dev --no-cache
RUN pip install gunicorn


CMD ["bash", "./app/start-prod.sh"]
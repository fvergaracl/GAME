FROM python:3.14-slim


WORKDIR /app

COPY health_check.py .

RUN pip3 install requests psycopg2-binary

CMD ["sh", "-c", "python3 health_check.py"]

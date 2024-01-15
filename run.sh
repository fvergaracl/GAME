poetry shell
docker-compose up --build -d
python3 main.py --env local --debug


# alembic revision --autogenerate -m "xxxxxxxxxxx"
# alembic upgrade head

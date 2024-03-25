import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

ENV: str = ""


class Configs(BaseSettings):
    # base
    ENV: str = os.getenv("ENV", "dev")
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GAME-api"
    GAMIFICATIONENGINE_VERSION_APP: str = os.getenv(
        "GAMIFICATIONENGINE_VERSION_APP", "No_version"
    )
    ENV_DATABASE_MAPPER: dict = {
        "prod": "game_dev_db",
        "stage": "game_dev_db",
        "dev": "game_dev_db",
        "test": "test_game_dev_db",
    }
    DEFAULT_CONVERTION_RATE_POINTS_TO_COIN: int = os.getenv(
        "DEFAULT_CONVERTION_RATE_POINTS_TO_COIN", 100
    )
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # database
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_ENGINE: str = os.getenv("DB_ENGINE", "postgresql")

    DATABASE_URI = "{db_engine}://{user}:{password}@{host}:{port}/{database}".format(
        db_engine=DB_ENGINE,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=ENV_DATABASE_MAPPER[ENV],
    )

    # find query
    PAGE = 1
    PAGE_SIZE = 10
    ORDERING = "-id"


class TestConfigs(Configs):
    ENV: str = "test"


configs = Configs()

if ENV == "prod":
    pass
elif ENV == "stage":
    pass
elif ENV == "test":
    configs = TestConfigs()

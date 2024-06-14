import os
from typing import List

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

ENV: str = ""


class Configs(BaseSettings):
    """
    Configuration class for loading environment variables and application
      settings.

    Attributes:
        ENV (str): The environment setting (e.g., 'dev', 'prod').
        API_V1_STR (str): The API version string.
        PROJECT_NAME (str): The name of the project.
        GAMIFICATIONENGINE_VERSION_APP (str): The version of the gamification
          engine application.
        ENV_DATABASE_MAPPER (dict): A mapping of environments to database
          names.
        DEFAULT_CONVERTION_RATE_POINTS_TO_COIN (int): The default conversion
          rate from points to coins.
        BACKEND_CORS_ORIGINS (List[str]): A list of allowed CORS origins.
        DB_USER (str): The database user.
        DB_PASSWORD (str): The database password.
        DB_HOST (str): The database host.
        DB_PORT (str): The database port.
        DB_ENGINE (str): The database engine.
        DATABASE_URI (str): The URI for the database connection.
        PAGE (int): The default page number for queries.
        PAGE_SIZE (int): The default page size for queries.
        ORDERING (str): The default ordering for queries.
    """

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

    DATABASE_URI = "{db_engine}://{user}:{password}@{host}:{port}/{database}".format(  # noqa: E501
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
    """
    Test configuration class for loading test environment settings.
    Inherits from Configs.

    Attributes:
        ENV (str): The environment setting for test environment.
    """

    ENV: str = "test"


configs = Configs()

if ENV == "prod":
    pass
elif ENV == "stage":
    pass
elif ENV == "test":
    configs = TestConfigs()

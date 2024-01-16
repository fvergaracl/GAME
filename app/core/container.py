from dependency_injector import containers, providers

from app.core.config import configs
from app.core.database import Database
from app.repository import *
from app.services import *


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.endpoints.games",
        ]
    )

    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    game_repository = providers.Factory(
        GameRepository, session_factory=db.provided.session)

    game_service = providers.Factory(
        GameService, game_repository=game_repository)

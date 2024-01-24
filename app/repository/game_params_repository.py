from contextlib import AbstractContextManager
from typing import Callable
from sqlalchemy.orm import Session, joinedload
from app.model.game_params import GamesParams
from app.repository.base_repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.schema.games_params_schema import BaseGameParams


class GameParamsRepository(BaseRepository):
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], model=GamesParams) -> None:
        super().__init__(session_factory, model)

    def update_params_gameId(self, gameId: int, param: BaseGameParams):
        with self.session_factory() as session:
            # Obtener el modelo de SQLAlchemy correspondiente
            game_param_model = session.query(self.model).filter(
                self.model.gameId == gameId,
                self.model.id == param.id
            ).first()

            if game_param_model:
                # Actualizar los campos del modelo SQLAlchemy con los datos del esquema Pydantic
                for key, value in param.dict(exclude_none=True).items():
                    setattr(game_param_model, key, value)

                # Confirmar la transacción
                session.commit()

                # Devolver el modelo actualizado
                # Asegúrate de que `read_by_id` devuelve una representación adecuada del modelo
                return self.read_by_id(
                    game_param_model.id, not_found_message=f"GameParams not found (id) : {game_param_model.id}")
            raise NotFoundError(
                f"GameParams not found (id) : {param.id}")

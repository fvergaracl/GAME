from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

from app.schema.games_params_schema import CreateGameParams, UpdateGameParams
from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.util.schema import AllOptional


class BaseGame(BaseModel):
    externalGameId: str
    platform: str
    endDateTime: datetime

    class Config:
        orm_mode = True


class CreateGame(BaseModel):
    externalGameId: str
    platform: str
    endDateTime: Optional[datetime]
    params: Optional[List[CreateGameParams]]


class UpdateGame(BaseModel):
    externalGameId: Optional[str]
    platform: Optional[str]
    endDateTime: Optional[datetime]
    params: Optional[List[UpdateGameParams]]


class Game(ModelBaseInfo, BaseGame, metaclass=AllOptional):
    ...


class FindGame(FindBase, BaseGame, metaclass=AllOptional):
    ...


class FindGameByExternalId(FindBase, BaseGame, metaclass=AllOptional):
    externalGameId: str


class UpsertGame(BaseGame, metaclass=AllOptional):
    ...


class UpsertGameWithGameParams(BaseGame, metaclass=AllOptional):
    param: str
    value: str


class FindGameResult(BaseModel):
    founds: Optional[List[Game]]
    search_options: Optional[SearchOptions]

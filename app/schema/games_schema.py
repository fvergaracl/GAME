from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from app.schema.games_params_schema import (
    BaseFindGameParams,
    CreateGameParams,
    UpdateGameParams
)
from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.util.schema import AllOptional


class BaseGame(BaseModel):
    platform: str

    class Config:
        orm_mode = True


class BaseGameResult(BaseModel):
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    externalGameId: Optional[str] = None
    platform: Optional[str] = None
    endDateTime: Optional[datetime] = None
    params: Optional[List[BaseFindGameParams]] = None

    class Config:
        orm_mode = True


class PostCreateGame(BaseModel):
    externalGameId: str
    platform: str
    endDateTime: Optional[datetime]
    params: Optional[List[CreateGameParams]]


class PatchGame(BaseModel):
    externalGameId: Optional[str]
    platform: Optional[str]
    endDateTime: Optional[datetime]
    params: Optional[List[UpdateGameParams]]


class GameCreated(BaseGameResult):
    message: Optional[str] = "Successfully created"


class GameUpdated(BaseGameResult):
    message: Optional[str] = "Successfully updated"


class ResponsePatchGame(BaseGameResult):
    message: Optional[str] = "Successfully updated"


class UpdateGame(BaseModel):
    id: UUID
    externalGameId: Optional[str]
    platform: Optional[str]
    endDateTime: Optional[datetime]
    params: Optional[List[UpdateGameParams]]


class FindGameById(ModelBaseInfo):
    externalGameId: Optional[str]
    platform: Optional[str]
    endDateTime: Optional[datetime]
    params: Optional[List[UpdateGameParams]]

class FindTaskGameById(ModelBaseInfo):
    externalGameId: Optional[str]
    platform: Optional[str]
    endDateTime: Optional[datetime]
    tasks: Optional[List[UpdateGameParams]]


class Game(ModelBaseInfo, BaseGame, metaclass=AllOptional):
    ...


class PostFindGame(FindBase, BaseGame, metaclass=AllOptional):
    ...


class FindGameByExternalId(FindBase, BaseGame, metaclass=AllOptional):
    externalGameId: str


class UpsertGame(BaseGame, metaclass=AllOptional):
    ...


class UpsertGameWithGameParams(BaseGame, metaclass=AllOptional):
    paramKey: str
    value: str


class FindGameResult(BaseModel):
    items: Optional[List[BaseGameResult]]
    search_options: Optional[SearchOptions]

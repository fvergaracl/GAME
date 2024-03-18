from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.schema.games_params_schema import (
    BaseFindGameParams, CreateGameParams, UpdateGameParams
)
from app.util.schema import AllOptional


class BaseGame(BaseModel):
    platform: str

    class Config:  # noqa
        orm_mode = True  # noqa


class BaseGameResult(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    strategyId: Optional[str] = None
    externalGameId: Optional[str] = None
    platform: Optional[str] = None
    endDateTime: Optional[datetime] = None
    params: Optional[List[BaseFindGameParams]] = None

    class Config:  # noqa
        orm_mode = True  # noqa


class PostCreateGame(BaseModel):
    externalGameId: str
    platform: str
    strategyId: Optional[str] = "default"
    endDateTime: Optional[datetime]
    params: Optional[List[CreateGameParams]]

    def example():
        return {
            "externalGameId": "string",
            "platform": "string",
            "strategyId": "default",
            "endDateTime": "2024-03-12T11:04:55.425Z",
            "params": [
                {
                    "key": "variable_basic_points",
                    "value": 10
                }
            ]
        }


class PatchGame(BaseModel):
    strategyId: Optional[str]
    platform: Optional[str]
    endDateTime: Optional[datetime]
    params: Optional[List[UpdateGameParams]]


class GameCreated(BaseGameResult):
    message: Optional[str] = "Successfully created"


class ResponsePatchGame(BaseGameResult):
    message: Optional[str] = "Successfully updated"


class FindGameById(ModelBaseInfo):  # noqa
    externalGameId: Optional[str]
    platform: Optional[str]
    endDateTime: Optional[datetime]
    params: Optional[List[UpdateGameParams]]


class PostFindGame(FindBase, BaseGame, metaclass=AllOptional):  # noqa
    ...


class FindGameResult(BaseModel):
    items: Optional[List[BaseGameResult]]
    search_options: Optional[SearchOptions]

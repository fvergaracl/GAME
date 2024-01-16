from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.util.schema import AllOptional


class BaseGame(BaseModel):
    externalGameID: str
    platform: str
    endDateTime: datetime

    class Config:
        orm_mode = True


class Game(ModelBaseInfo, BaseGame, metaclass=AllOptional):
    ...


class FindGame(FindBase, BaseGame, metaclass=AllOptional):
    externalGameID__eq: str


class UpsertGame(BaseGame, metaclass=AllOptional):
    ...


class UpsertGameWithGameParams(BaseGame, metaclass=AllOptional):
    param: str
    value: str


class FindGameResult(BaseModel):
    founds: Optional[List[Game]]
    search_options: Optional[SearchOptions]

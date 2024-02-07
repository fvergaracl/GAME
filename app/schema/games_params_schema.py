from uuid import UUID

from pydantic import BaseModel


class BaseGameParams(BaseModel):
    paramKey: str
    value: str | int | float | bool

    class Config:
        orm_mode = True


class BaseCreateGameParams(BaseGameParams): ...


class InsertGameParams(BaseGameParams):
    gameId: str


class CreateGameParams(BaseCreateGameParams): ...


class BaseFindGameParams(BaseGameParams):
    ...
    id: UUID


class UpdateGameParams(CreateGameParams):
    id: UUID
    paramKey: str
    value: str | int | float | bool

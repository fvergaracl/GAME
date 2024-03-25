from uuid import UUID

from pydantic import BaseModel


class BaseGameParams(BaseModel):
    key: str
    value: str | int | float | bool

    class Config:  # noqa
        orm_mode = True  # noqa


class BaseCreateGameParams(BaseGameParams):
    ...


class InsertGameParams(BaseGameParams):
    gameId: str


class CreateGameParams(BaseCreateGameParams):
    ...


class BaseFindGameParams(BaseGameParams):
    ...
    id: UUID


class UpdateGameParams(CreateGameParams):
    id: UUID
    key: str
    value: str | int | float | bool

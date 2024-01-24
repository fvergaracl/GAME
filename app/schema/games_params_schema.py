from pydantic import BaseModel


class CreateGameParams(BaseModel):
    paramKey: str
    value: str | int | float | bool

    class Config:
        orm_mode = True


class BaseGameParams(CreateGameParams):
    gameId: int
    paramKey: str
    value: str | int | float | bool


class UpdateGameParams(CreateGameParams):
    id: int
    paramKey: str
    value: str | int | float | bool

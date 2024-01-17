from pydantic import BaseModel


class CreateGameParams(BaseModel):
    param: str
    value: str | int | float | bool

    class Config:
        orm_mode = True


class BaseGameParams(CreateGameParams):
    gameId: int
    param: str
    value: str | int | float | bool


class UpdateGameParams(CreateGameParams):
    id: int
    param: str
    value: str | int | float | bool

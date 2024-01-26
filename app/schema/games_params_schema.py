from pydantic import BaseModel


class BaseGameParams(BaseModel):
    paramKey: str
    value: str | int | float | bool

    class Config:
        orm_mode = True


class CreateGameParams(BaseGameParams):
    ...


class BaseGameParams(CreateGameParams):
    id: int
    paramKey: str
    value: str | int | float | bool


class UpdateGameParams(CreateGameParams):
    id: int
    paramKey: str
    value: str | int | float | bool

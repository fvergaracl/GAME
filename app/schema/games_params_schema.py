from pydantic import BaseModel


class BaseGameParams(BaseModel):
    gameID: int
    param: str
    value: str | int | float | bool

    class Config:
        orm_mode = True

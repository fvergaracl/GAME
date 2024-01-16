from pydantic import BaseModel


class BaseGameParams(BaseModel):
    param: str
    value: str | int | float | bool

    class Config:
        orm_mode = True

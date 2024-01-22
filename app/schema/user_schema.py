from pydantic import BaseModel


class BaseUser(BaseModel):
    externalUserId: str

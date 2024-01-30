from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo


class BaseUser(BaseModel):
    externalUserId: str


class PostCreateUser(BaseUser):
    ...


class CreatedUser(ModelBaseInfo, BaseUser):
    ...

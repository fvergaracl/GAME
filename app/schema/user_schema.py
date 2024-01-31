from pydantic import BaseModel
from app.schema.base_schema import ModelBaseInfo
from app.schema.user_points_schema import BaseUserPointsBaseModel
from app.schema.wallet_schema import Wallet
from uuid import UUID
from typing import Optional


class BaseUser(BaseModel):
    externalUserId: str


class PostCreateUser(BaseUser):
    ...


class CreatedUser(ModelBaseInfo, BaseUser):
    ...


class PostAssignPointsToUser(BaseModel):
    taskId: UUID
    points: int
    # allow json into description
    data: Optional[dict]


class CreateWallet(Wallet):
    ...

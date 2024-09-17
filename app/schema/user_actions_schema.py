from typing import List, Optional

from pydantic import BaseModel

from app.schema.base_schema import ModelBaseInfo
from app.schema.wallet_schema import WalletWithoutUserId
from app.util.schema import AllOptional


class UserActions(BaseModel):
    """
    Model for user actions

    Attributes:
        userId (str): User ID
        action (str): Action
        data (Optional[dict]): Additional data
        created_at (str): Created date
    """

    userId: str
    action: str
    data: Optional[dict]


class CreateUserActions(BaseModel):
    """
    Model for creating user actions

    Attributes:
        userId (str): User ID
        action (str): Action
        data (Optional[dict]): Additional data
    """

    typeAction: str
    data: Optional[dict]
    description: Optional[str]
    userId: str

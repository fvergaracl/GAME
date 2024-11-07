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


class CreateUserBodyActions(BaseModel):
    """
    Model for creating user actions

    Attributes:
        typeAction (str): Action type
        data (Optional[dict]): Additional data in json format
        description (Optional[str]): Description of the action
        apiKey_used (Optional[str]): API key used
    """

    typeAction: str
    data: Optional[dict]
    description: Optional[str]
    apiKey_used: Optional[str]


class CreateUserActions(CreateUserBodyActions):
    """
    Model for creating user actions

    Attributes:
        typeAction (str): Action type
        data (Optional[dict]): Additional data in json format
        description (Optional[str]): Description of the action
        apiKey_used (Optional[str]): API key used
        userId (str): User ID

    """

    userId: str


class CreatedUserActions(BaseModel):
    """
    Model for created user actions

    Attributes:
        userId (str): User ID
        action (str): Action
        data (Optional[dict]): Additional data
        created_at (str): Created date
    """

    typeAction: str
    description: Optional[str]
    userId: str
    is_user_created: Optional[bool]
    message: str

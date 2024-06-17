from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schema.base_schema import ModelBaseInfo
from app.schema.task_schema import TaskPointsResponseByUser
from app.schema.wallet_schema import WalletWithoutUserId
from app.schema.wallet_transaction_schema import BaseWalletTransactionInfo


class BaseUser(BaseModel):
    """
    Base model for a user

    Attributes:
        externalUserId (str): External user ID
    """
    externalUserId: str


class UserBasicInfo(ModelBaseInfo, BaseUser):  # noqa
    """Model for basic user information."""
    ...


class PostAssignPointsToUser(BaseModel):
    """
    Model for assigning points to a user

    Attributes:
        taskId (UUID): Task ID
        points (Optional[int]): Points
        description (Optional[str]): Description
        data (Optional[dict]): Additional data
    """
    taskId: UUID
    points: Optional[int]
    description: Optional[str]
    data: Optional[dict]


class UserWallet(BaseModel):
    """
    Model for a user wallet

    Attributes:
        userId (str): User ID
        wallet (Optional[WalletWithoutUserId]): Wallet
        walletTransactions (Optional[list[BaseWalletTransactionInfo]]): Wallet
          transactions
    """
    userId: str
    wallet: Optional[WalletWithoutUserId]
    walletTransactions: Optional[list[BaseWalletTransactionInfo]]


class UserPointsTasks(BaseModel):
    """
    Model for user points tasks

    Attributes:
        id (UUID): Unique identifier
        tasks (list[TaskPointsResponseByUser]): List of tasks
    """
    id: UUID
    tasks: list[TaskPointsResponseByUser]


class ResponseConversionPreview(BaseModel):
    """
    Model for conversion preview response

    Attributes:
        points (int): Points
        conversionRate (float): Conversion rate
        conversionRateDate (str): Conversion rate date
        convertedAmount (float): Converted amount
        convertedCurrency (str): Converted currency
        haveEnoughPoints (bool): If the user has enough points
    """
    points: int
    conversionRate: float
    conversionRateDate: str
    convertedAmount: float
    convertedCurrency: str
    haveEnoughPoints: bool


class PostPointsConversionRequest(BaseModel):
    """
    Model for points conversion request

    Attributes:
        points (int): Points
    """
    points: int


class ResponsePointsConversion(BaseModel):
    """
    Model for points conversion response

    Attributes:
        transactionId (str): Transaction ID
        points (int): Points
        conversionRate (float): Conversion rate
        conversionRateDate (str): Conversion rate date
        convertedAmount (float): Converted amount
        convertedCurrency (str): Converted currency
        haveEnoughPoints (bool): If the user has enough points
    """
    transactionId: str
    points: int
    conversionRate: float
    conversionRateDate: str
    convertedAmount: float
    convertedCurrency: str
    haveEnoughPoints: bool

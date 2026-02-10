from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schema.base_schema import ModelBaseInfo
from app.schema.task_schema import TaskPointsResponseByUser
from app.schema.wallet_schema import WalletWithoutUserId
from app.schema.wallet_transaction_schema import BaseWalletTransactionInfo


class BaseUser(BaseModel):
    """
    Base schema identifying a user by external identifier.

    Attributes:
        externalUserId (str): Consumer-facing user identifier from the client
          system.
    """

    externalUserId: str = Field(
        ...,
        description="External identifier of the user in the client platform.",
        example="user-12345",
    )


class UserBasicInfo(ModelBaseInfo, BaseUser):  # noqa
    """
    Base response schema containing persisted user metadata and external ID.
    """

    ...


class PostAssignPointsToUser(BaseModel):
    """
    Request schema to assign points to a user for a specific task.

    Attributes:
        taskId (UUID): Internal task UUID.
        points (Optional[int]): Points to assign.
        description (Optional[str]): Human-readable assignment reason.
        data (Optional[dict]): Extra structured metadata.
    """

    taskId: UUID = Field(
        ...,
        description="Internal UUID of the target task.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    points: Optional[int] = Field(
        default=None,
        description="Points to assign for this operation.",
        example=100,
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable reason for awarding points.",
        example="Good job",
    )
    data: Optional[dict] = Field(
        default=None,
        description="Additional metadata related to this assignment.",
        example={"extra": "value"},
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative payload for user point assignment.
        """
        return {
            "taskId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
            "points": 100,
            "description": "Good job",
            "data": {"extra": "value"},
        }


class PostAssignPointsToUserWithCaseName(PostAssignPointsToUser):
    """
    Request schema for external point assignment including explicit case name.

    Attributes:
        taskId (str): External task identifier.
        caseName (str): Strategy/incentive case label to apply.
    """

    taskId: str = Field(
        ...,
        description="External task identifier from the client system.",
        example="task-eco-action-01",
    )
    caseName: str = Field(
        ...,
        description="Case label used by scoring/adaptive strategy rules.",
        example="TASK_COMPLETION",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative payload for external points assignment.
        """
        return {
            "taskId": "task-eco-action-01",
            "caseName": "TASK_COMPLETION",
            "points": 100,
            "description": "Good job",
            "data": {"extra": "value"},
        }


class UserWallet(BaseModel):
    """
    Response schema containing user wallet and transaction history.

    Attributes:
        userId (str): Internal user UUID as string.
        wallet (Optional[WalletWithoutUserId]): Current wallet balances.
        walletTransactions (Optional[list[BaseWalletTransactionInfo]]):
          User wallet transaction history.
    """

    userId: str = Field(
        ...,
        description="Internal UUID of the user (serialized as string).",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )
    wallet: Optional[WalletWithoutUserId] = Field(
        default=None,
        description="Current wallet snapshot for the user.",
    )
    walletTransactions: Optional[list[BaseWalletTransactionInfo]] = Field(
        default=None,
        description="Chronological transaction entries for the user's wallet.",
    )


class UserPointsTasks(BaseModel):
    """
    Response schema listing points earned per task for a user.

    Attributes:
        id (UUID): Internal user UUID.
        tasks (list[TaskPointsResponseByUser]): Task-level points entries.
    """

    id: UUID = Field(
        ...,
        description="Internal UUID of the user.",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )
    tasks: list[TaskPointsResponseByUser] = Field(
        ...,
        description="List of tasks with points values for this user.",
    )


class ResponseConversionPreview(BaseModel):
    """
    Response schema for points-to-coins conversion preview.

    Attributes:
        points (int): Requested points to convert.
        conversionRate (float): Applied conversion rate.
        conversionRateDate (str): Date of the applied conversion rate.
        convertedAmount (float): Resulting coin amount.
        convertedCurrency (str): Currency/unit of converted amount.
        haveEnoughPoints (bool): Whether user balance can cover conversion.
    """

    points: int = Field(
        ...,
        description="Requested number of points for preview conversion.",
        example=100,
    )
    conversionRate: float = Field(
        ...,
        description="Conversion rate applied to the request.",
        example=1.5,
    )
    conversionRateDate: str = Field(
        ...,
        description="Date when the conversion rate became effective.",
        example="2026-02-10",
    )
    convertedAmount: float = Field(
        ...,
        description="Estimated converted amount (coins/currency).",
        example=150.0,
    )
    convertedCurrency: str = Field(
        ...,
        description="Currency or coin unit for converted amount.",
        example="USD",
    )
    haveEnoughPoints: bool = Field(
        ...,
        description="True when the user has enough points to convert.",
        example=True,
    )


class PostPointsConversionRequest(BaseModel):
    """
    Request schema to convert user points into coins/currency.

    Attributes:
        points (int): Number of points requested for conversion.
    """

    points: int = Field(
        ...,
        description="Number of points to convert.",
        example=100,
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative conversion request payload.
        """
        return {"points": 100}


class ResponsePointsConversion(BaseModel):
    """
    Response schema returned after points conversion execution.

    Attributes:
        transactionId (str): Identifier of the created conversion transaction.
        points (int): Converted points.
        conversionRate (float): Applied conversion rate.
        conversionRateDate (str): Date of the conversion rate used.
        convertedAmount (float): Final converted amount.
        convertedCurrency (str): Currency/unit of converted amount.
        haveEnoughPoints (bool): Whether the user had enough points.
    """

    transactionId: str = Field(
        ...,
        description="Unique identifier of the conversion transaction.",
        example="txn_018f59df7a7e",
    )
    points: int = Field(
        ...,
        description="Points converted in the transaction.",
        example=100,
    )
    conversionRate: float = Field(
        ...,
        description="Conversion rate applied to the transaction.",
        example=1.5,
    )
    conversionRateDate: str = Field(
        ...,
        description="Date when the applied conversion rate is valid.",
        example="2026-02-10",
    )
    convertedAmount: float = Field(
        ...,
        description="Amount obtained after conversion.",
        example=150.0,
    )
    convertedCurrency: str = Field(
        ...,
        description="Currency or coin unit for the converted amount.",
        example="USD",
    )
    haveEnoughPoints: bool = Field(
        ...,
        description="True when conversion was allowed by balance checks.",
        example=True,
    )

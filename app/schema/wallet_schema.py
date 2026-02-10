from typing import Optional

from pydantic import BaseModel, Field

from app.schema.base_schema import ModelBaseInfo


class WalletWithoutUserId(BaseModel):
    """
    Wallet balance schema without user identifier.

    Used in nested responses where user identity is already implied by route or
    parent object.

    Attributes:
        coinsBalance (Optional[float]): Current coin/currency balance.
        pointsBalance (Optional[float]): Current points balance.
        conversionRate (Optional[float]): Active points-to-coins conversion rate.
    """

    coinsBalance: Optional[float] = Field(
        default=None,
        description="Current coin or currency balance.",
        example=100.0,
    )
    pointsBalance: Optional[float] = Field(
        default=None,
        description="Current points balance.",
        example=200.0,
    )
    conversionRate: Optional[float] = Field(
        default=None,
        description="Current conversion rate used to transform points into coins.",
        example=1.5,
    )


class Wallet(WalletWithoutUserId):
    """
    Wallet schema including user identity.

    Attributes:
        userId (Optional[str]): Internal user UUID serialized as string.
    """

    userId: Optional[str] = Field(
        default=None,
        description="Internal UUID of the wallet owner (serialized as string).",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )


class BaseWallet(ModelBaseInfo):
    """
    Persisted wallet record schema with metadata.

    Attributes:
        coinsBalance (Optional[float]): Current coin/currency balance.
        pointsBalance (Optional[float]): Current points balance.
        conversionRate (Optional[float]): Active points-to-coins conversion rate.
        userId (Optional[int]): Internal numeric user identifier (legacy/internal).
    """

    coinsBalance: Optional[float] = Field(
        default=None,
        description="Current coin or currency balance.",
        example=100.0,
    )
    pointsBalance: Optional[float] = Field(
        default=None,
        description="Current points balance.",
        example=200.0,
    )
    conversionRate: Optional[float] = Field(
        default=None,
        description="Current conversion rate applied for points conversion.",
        example=1.5,
    )
    userId: Optional[int] = Field(
        default=None,
        description="Internal numeric identifier of the wallet owner.",
        example=123,
    )


class BaseWalletOnlyUserId(BaseModel):
    """
    Lightweight wallet schema for user-centric balance operations.

    Attributes:
        userId (int): Internal numeric user identifier.
        pointsBalance (Optional[float]): Points balance for the user.
    """

    userId: int = Field(
        ...,
        description="Internal numeric identifier of the user.",
        example=123,
    )
    pointsBalance: Optional[float] = Field(
        default=None,
        description="Current points balance for the user.",
        example=200.0,
    )


class PostPreviewConvertPoints(BaseModel):
    """
    Request schema to preview points-to-coins conversion.

    Attributes:
        points (float): Number of points requested for conversion preview.
        externalUserId (str): Consumer-facing user identifier.
    """

    points: float = Field(
        ...,
        description="Number of points to preview for conversion.",
        example=100.0,
    )
    externalUserId: str = Field(
        ...,
        description="External user identifier from the client platform.",
        example="user-12345",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative conversion-preview payload.
        """
        return {"points": 100.0, "externalUserId": "user-12345"}


class ResponsePreviewConvertPoints(BaseModel):
    """
    Response schema for points conversion preview.

    Attributes:
        coins (float): Estimated coins/currency that would be received.
        points_converted (float): Number of points considered for conversion.
        conversionRate (float): Conversion rate applied in preview.
        afterConversionPoints (float): Projected points balance after conversion.
        afterConversionCoins (float): Projected coins balance after conversion.
        externalUserId (str): Consumer-facing user identifier.
    """

    coins: float = Field(
        ...,
        description="Estimated coins/currency resulting from conversion.",
        example=50.0,
    )
    points_converted: float = Field(
        ...,
        description="Points that would be converted.",
        example=100.0,
    )
    conversionRate: float = Field(
        ...,
        description="Conversion rate used for preview calculation.",
        example=1.5,
    )
    afterConversionPoints: float = Field(
        ...,
        description="Projected points balance after conversion.",
        example=200.0,
    )
    afterConversionCoins: float = Field(
        ...,
        description="Projected coins/currency balance after conversion.",
        example=75.0,
    )
    externalUserId: str = Field(
        ...,
        description="External user identifier for whom conversion is previewed.",
        example="user-12345",
    )


class CreateWallet(Wallet):
    """
    Request schema for wallet creation.

    Attributes:
        apiKey_used (Optional[str]): API key used by the caller (if applicable).
    """

    apiKey_used: Optional[str] = Field(
        default=None,
        description="API key used to create the wallet when API-key auth is used.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative wallet-creation payload.
        """
        return {
            "coinsBalance": 100.0,
            "pointsBalance": 200.0,
            "conversionRate": 1.5,
            "userId": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
        }

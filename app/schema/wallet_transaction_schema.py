from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseWalletTransactionWithoutWalletId(BaseModel):
    """
    Base wallet transaction schema without wallet linkage.

    This schema is used in contexts where transaction payload is known but the
    wallet owner is derived from route context or parent objects.

    Attributes:
        transactionType (str): Transaction category/type.
        points (int): Points affected by the transaction.
        coins (float): Coin/currency amount affected by the transaction.
        data (Optional[dict]): Additional metadata for audit and diagnostics.
    """

    transactionType: str = Field(
        ...,
        description="Transaction type (for example conversion, reward, refund).",
        example="conversion",
    )
    points: int = Field(
        ...,
        description="Number of points credited/debited in the transaction.",
        example=100,
    )
    coins: float = Field(
        ...,
        description="Coin/currency amount credited/debited in the transaction.",
        example=50.0,
    )
    data: Optional[dict] = Field(
        default=None,
        description="Additional transaction metadata.",
        example={"reason": "manual-adjustment", "source": "admin-panel"},
    )


class BaseWalletTransaction(BaseWalletTransactionWithoutWalletId):
    """
    Wallet transaction schema including wallet linkage and conversion metadata.

    Attributes:
        walletId (str): Internal wallet UUID (serialized as string).
        appliedConversionRate (float): Conversion rate used for this transaction.
        apiKey_used (Optional[str]): API key used by caller when applicable.
    """

    walletId: str = Field(
        ...,
        description="Internal UUID of the wallet associated with this transaction.",
        example="fd8551f4-7cf0-4f8b-b372-a269541db5a5",
    )
    appliedConversionRate: float = Field(
        ...,
        description="Conversion rate applied to compute coins from points.",
        example=1.5,
    )
    apiKey_used: Optional[str] = Field(
        default=None,
        description="API key used to submit the transaction request, if available.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative wallet transaction payload.
        """
        return {
            "transactionType": "conversion",
            "points": 100,
            "coins": 50.0,
            "data": {"reason": "manual-adjustment", "source": "admin-panel"},
            "walletId": "fd8551f4-7cf0-4f8b-b372-a269541db5a5",
            "appliedConversionRate": 1.5,
        }


class BaseWalletTransactionInfo(BaseWalletTransactionWithoutWalletId):
    """
    Read-only wallet transaction schema enriched with persisted metadata.

    Attributes:
        id (UUID): Unique transaction identifier.
        created_at (str): UTC creation timestamp in ISO-8601 format.
    """

    id: UUID = Field(
        ...,
        description="Unique UUID of the wallet transaction record.",
        example="a20ed58b-f9d2-45fa-bb63-88572745ef5a",
    )
    created_at: str = Field(
        ...,
        description="Transaction creation timestamp (ISO-8601 UTC string).",
        example="2026-02-10T12:20:00Z",
    )

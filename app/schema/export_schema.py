from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class ExportDatasetType(str, Enum):
    USERS = "users"
    USER_POINTS = "user-points"
    USER_INTERACTIONS = "user-interactions"
    WALLET_TRANSACTIONS = "wallet-transactions"


class ExportStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFilters(BaseModel):
    """
    Query filters accepted by every /v1/exports/* endpoint.
    """

    externalGameId: Optional[str] = Field(
        default=None,
        description="Filter rows by externalGameId.",
        examples=["game-readme-001"],
    )
    externalTaskId: Optional[str] = Field(
        default=None,
        description="Filter rows by externalTaskId.",
        examples=["task-login"],
    )
    dateFrom: Optional[datetime] = Field(
        default=None,
        description="Inclusive lower bound for created_at (ISO 8601).",
        examples=["2026-01-01T00:00:00Z"],
    )
    dateTo: Optional[datetime] = Field(
        default=None,
        description="Inclusive upper bound for created_at (ISO 8601).",
        examples=["2026-02-01T00:00:00Z"],
    )
    limit: int = Field(
        default=10_000,
        ge=1,
        le=100_000,
        description="Maximum number of rows to emit.",
        examples=[10_000],
    )


class CreateExportAuditLog(BaseModel):
    """
    Internal schema used to persist a new ExportAuditLog row when the export
    request is accepted (before streaming starts).
    """

    datasetType: str
    format: str
    filters: dict
    rowLimit: int
    rowCount: int = -1
    status: str = ExportStatus.STARTED.value
    requestedBy: Optional[str] = None
    apiKey_used: Optional[str] = None
    oauth_user_id: Optional[str] = None

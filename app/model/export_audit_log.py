from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Integer, String

from app.model.base_model import BaseModel
from pydantic import ConfigDict


class ExportAuditLog(BaseModel, table=True):
    """
    Records every data export request made through /v1/exports.

    Written at the moment the streaming response starts so that interrupted
    downloads are still auditable.

    Attributes:
        datasetType (str): Dataset exported ("users", "user-points",
          "user-interactions", "wallet-transactions").
        format (str): Output format ("csv", "xlsx", "json").
        filters (dict): Filter parameters used (gameId, taskId, dateFrom,
          dateTo, limit) serialized as JSON.
        rowLimit (int): Effective row cap applied to the query.
        rowCount (int): Rows actually emitted; -1 while streaming, set on
          completion when the caller closes the stream cleanly.
        status (str): One of "started", "completed", "failed".
        requestedBy (str): Best-effort identifier for who triggered it
          (oauth sub or api key prefix).
    """

    datasetType: str = Field(sa_column=Column(String, nullable=False))
    format: str = Field(sa_column=Column(String, nullable=False))
    filters: dict = Field(sa_column=Column(JSONB, nullable=True))
    rowLimit: int = Field(sa_column=Column(Integer, nullable=False))
    rowCount: int = Field(sa_column=Column(Integer, nullable=False, default=-1))
    status: str = Field(sa_column=Column(String, nullable=False, default="started"))
    requestedBy: str = Field(sa_column=Column(String, nullable=True))

    model_config = ConfigDict(from_attributes=True)

    def __str__(self):
        return (
            f"ExportAuditLog (id={self.id}, datasetType={self.datasetType}, "
            f"format={self.format}, status={self.status}, "
            f"rowCount={self.rowCount}, requestedBy={self.requestedBy})"
        )

    def __repr__(self):
        return self.__str__()

from sqlmodel import (
    Column, Field, String, Integer
)
from app.model.base_model import BaseModel


class KpiMetrics(BaseModel, table=True):
    """
    Represents a KPI metrics entity.

    Attributes:
        day (str): Day of the metrics period (e.g., 2021-01-01).
        totalRequests (int): Total requests in the period.
        successRate (float): Success rate of the requests.
        avgLatencyMS (float): Average latency in ms.
        errorRate (float): Error rate in percentage.
        activeUsers (int): Number of active users in the period.
        retentionRate (float): User retention rate.
        avgInteractionsPerUser (float): Average number of interactions per
          user.
    """

    day: str = Field(sa_column=Column(String))
    totalRequests: int = Field(sa_column=Column(Integer))
    successRate: float = Field(sa_column=Column(Integer))
    avgLatencyMS: float = Field(sa_column=Column(Integer))
    errorRate: float = Field(sa_column=Column(Integer))
    activeUsers: int = Field(sa_column=Column(Integer))
    retentionRate: float = Field(sa_column=Column(Integer))
    avgInteractionsPerUser: float = Field(sa_column=Column(Integer))

    class Config:
        orm_mode = True

    def __str__(self):
        """
        Returns a string representation of the object.

        Returns:
            str: A string representation of the object.
        """
        return (
            f"KpiMetrics: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, day={self.day}, "
            f"totalRequests={self.totalRequests}, successRate="
            f"{self.successRate}, avgLatencyMS={self.avgLatencyMS}, "
            f"errorRate={self.errorRate}, activeUsers={self.activeUsers}, "
            f"retentionRate={self.retentionRate}, "
            f"avgInteractionsPerUser={self.avgInteractionsPerUser})"
        )

    def __repr__(self):
        """
        Returns a string representation of the object.

        Returns:
            str: A string representation of the object.
        """
        return self.__str__()

    def __eq__(self, other):
        """
        Compares two objects for equality.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        return (
            isinstance(other, KpiMetrics)
            and self.day == other.day
            and self.totalRequests == other.totalRequests
            and self.successRate == other.successRate
            and self.avgLatencyMS == other.avgLatencyMS
            and self.errorRate == other.errorRate
            and self.activeUsers == other.activeUsers
            and self.retentionRate == other.retentionRate
            and self.avgInteractionsPerUser == other.avgInteractionsPerUser
        )

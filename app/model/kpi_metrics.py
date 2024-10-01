from sqlmodel import (
    Column, Field, SQLModel, String, Integer
)


class KPIMetrics(SQLModel, table=True):
    """
    Represents a KPI metrics entity.

    Attributes:
        day (str): Day of the metrics period (e.g., 2021-01-01).
        total_requests (int): Total requests in the period.
        success_rate (float): Success rate of the requests.
        avg_latency_ms (float): Average latency in ms.
        error_rate (float): Error rate in percentage.
        active_users (int): Number of active users in the period.
        retention_rate (float): User retention rate.
        avg_interactions_per_user (float): Average number of interactions per
          user.
    """

    day: str = Field(sa_column=Column(String))
    total_requests: int = Field(sa_column=Column(Integer))
    success_rate: float = Field(sa_column=Column(Integer))
    avg_latency_ms: float = Field(sa_column=Column(Integer))
    error_rate: float = Field(sa_column=Column(Integer))
    active_users: int = Field(sa_column=Column(Integer))
    retention_rate: float = Field(sa_column=Column(Integer))
    avg_interactions_per_user: float = Field(sa_column=Column(Integer))

    class Config:
        orm_mode = True

    def __str__(self):
        """
        Returns a string representation of the object.

        Returns:
            str: A string representation of the object.
        """
        return (
            f"KPIMetrics: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, day={self.day}, "
            f"total_requests={self.total_requests}, success_rate="
            f"{self.success_rate}, avg_latency_ms={self.avg_latency_ms}, "
            f"error_rate={self.error_rate}, active_users={self.active_users}, "
            f"retention_rate={self.retention_rate}, "
            f"avg_interactions_per_user={self.avg_interactions_per_user})"
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
            isinstance(other, KPIMetrics)
            and self.day == other.day
            and self.total_requests == other.total_requests
            and self.success_rate == other.success_rate
            and self.avg_latency_ms == other.avg_latency_ms
            and self.error_rate == other.error_rate
            and self.active_users == other.active_users
            and self.retention_rate == other.retention_rate
            and self.avg_interactions_per_user == other.avg_interactions_per_user
        )

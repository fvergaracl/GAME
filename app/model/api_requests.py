from sqlmodel import (
    Column, Field, SQLModel, String, Integer, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID


class ApiRequests(SQLModel, table=True):
    """
    Represents an API request entity.

    Attributes:
        userId (str): The ID of the user associate with the request.
        endpoint (str): API endpoint name.
        statusCode (int): HTTP response code.
        responseTimeMS (int): Response time in milliseconds.
        requestType (str): Request type (GET, POST, etc.).

    """

    userId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("users.id")))
    endpoint: str = Field(sa_column=Column(String))
    statusCode: int = Field(sa_column=Column(Integer))
    responseTimeMS: int = Field(sa_column=Column(Integer))
    requestType: str = Field(sa_column=Column(String))

    class Config:
        orm_mode = True

    def __str__(self):
        """
        Returns a string representation of the object.

        Returns:
            str: A string representation of the object.
        """
        return (
            f"ApiRequests: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, userId={self.userId}, "
            f"endpoint={self.endpoint}, statusCode={self.statusCode}, "
            f"responseTimeMS={self.responseTimeMS}, "
            f"requestType={self.requestType})"
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
            isinstance(other, ApiRequests)
            and self.userId == other.userId
            and self.endpoint == other.endpoint
            and self.statusCode == other.statusCode
            and self.responseTimeMS == other.responseTimeMS
            and self.requestType == other.requestType
        )

from sqlmodel import Column, Field, String

from app.model.base_model import BaseModel


class UptimeLogs(BaseModel, table=True):
    """

    Represents an uptime log entity.

    Attributes:
        status (str): Status of the service (up or down).
    """

    status: str = Field(sa_column=Column(String))

    class Config:
        orm_mode = True

    def __str__(self):
        """
        Returns a string representation of the object.

        Returns:
            str: A string representation of the object.
        """
        return (
            f"UptimeLogs: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, status={self.status})"
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
            other (object): The object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        return isinstance(other, UptimeLogs) and self.status == other.status

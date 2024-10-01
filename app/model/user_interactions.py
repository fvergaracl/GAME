from sqlalchemy.dialects.postgresql import UUID
from app.model.base_model import BaseModel
from sqlmodel import (
    Column, Field, String, Integer, ForeignKey
)


class UserInteractions(BaseModel, table=True):
    """
    Represents a user interaction entity.

    Attributes:
        userId (str): The ID of the user associated with the interaction.
        taskId (str): The ID of the task associated with the interaction.
        interactionType (str): The type of interaction (e.g., achievement,
          task).
        interactionDetail (str): Description of the achievement or task (e.g.,
          task completed, achievement unlocked).
    """

    userId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True))
    taskId: str = Field(sa_column=Column(
        UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True))
    interactionType: str = Field(sa_column=Column(String))
    interactionDetail: str = Field(sa_column=Column(String))

    class Config:
        orm_mode = True

    def __str__(self):
        """
        Returns a string representation of the object.

        Returns:
            str: A string representation of the object.
        """
        return (
            f"UserInteractions: (id={self.id}, created_at={self.created_at}, "
            f"updated_at={self.updated_at}, userId={self.userId}, "
            f"interactionType={self.interactionType}, "
            f"interactionDetail={self.interactionDetail})"
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
        return (
            isinstance(other, UserInteractions)
            and self.userId == other.userId
            and self.interactionType == other.interactionType
            and self.interactionDetail == other.interactionDetail
        )

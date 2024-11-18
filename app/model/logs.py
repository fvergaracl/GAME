from sqlmodel import Column, Field, String, JSON, TIMESTAMP
from app.model.base_model import BaseModel


class Logs(BaseModel, table=True):
    """
    Represents a general log entry in the system.

    Attributes:
        log_level (str): The severity level of the log (e.g., 'info',
          'warning', 'error').
        message (str): The descriptive message of the log entry.
        module (str): The module or component that generated the log.
        details (dict): Additional details about the log, stored in JSON
          format.

    Methods:
        __str__: Return a string representation of the object.
        __repr__: Return a string representation of the object.
        __eq__: Compare if two objects are equal.
        __hash__: Return the hash of the object.

    """

    log_level: str = Field(sa_column=Column(String))
    message: str = Field(sa_column=Column(String))
    module: str = Field(sa_column=Column(String), nullable=True)
    details: dict = Field(sa_column=Column(JSON), nullable=True)

    class Config:  # noqa
        orm_mode = True  # noqa

    def __str__(self):
        return (
            f"Logs: (id={self.id}, log_level={self.log_level}, "
            f"message={self.message}, module={self.module}, "
            f"details={self.details}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def __repr__(self):
        return (
            f"Logs: (id={self.id}, log_level={self.log_level}, "
            f"message={self.message}, module={self.module}, "
            f"details={self.details}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def __eq__(self, other):
        return (
            isinstance(other, Logs)
            and self.log_level == other.log_level
            and self.message == other.message
            and self.module == other.module
            and self.details == other.details
        )

    def __hash__(self):
        return hash(
            (
                self.log_level,
                self.message,
                self.module,
                str(self.details),
            )
        )

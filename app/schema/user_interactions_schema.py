from pydantic import BaseModel


class UserInteractionsBase(BaseModel):
    """
    Base model for user's interactions
    """

    userId: str
    taskId: str
    interactionType: str
    interactionDetail: str

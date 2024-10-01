from pydantic import BaseModel


class UserInteractionsBase(BaseModel):
    """
    Base model for user's interactions
    """

    user_id: str
    task_id: str

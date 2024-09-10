from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel


class ApikeyBase(BaseModel):
    """
    Base model for ApiKey
    """
    key: UUID
    description: Optional[str]
    active: bool
    createdBy: str

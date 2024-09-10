from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel


class ApikeyBase(BaseModel):
    """
    Base model for ApiKey
    """
    apiKey: str


class ApiKeyPostBody(ApikeyBase):
    """
    Model for creating a new API key
    """
    client: str
    description: str


class ApiKeyCreate(ApiKeyPostBody):
    """
    Model for creating a new API key with createdBy field
    """
    createdBy: str


class ApiKeyCreated(ApikeyBase):
    """
    Model for creating a new API key
    """
    apiKey: str
    client: str
    description: str
    createdBy: str
    message: Optional[str]

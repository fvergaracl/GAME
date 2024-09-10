from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel


class ApikeyBase(BaseModel):
    """
    Base model for ApiKey
    """
    apiKey: str


class ApiKeyPostBody(BaseModel):
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
    apiKey: str


class ApiKeyCreateBase(ApikeyBase):
    """
    Model for creating a new API key
    """
    apiKey: str
    client: str
    description: str
    createdBy: str


class ApiKeyCreatedUnitList(ApiKeyCreateBase):
    """
    Model for creating a new API key 
    """
    created_at: datetime


class ApiKeyCreated(ApiKeyCreateBase):
    """
    Model for creating a new API key
    """
    message: Optional[str]

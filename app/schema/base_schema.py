from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel


class RootEndpoint(BaseModel):
    """
    Root API v1 endpoint

    Attributes:
        projectName (str): Name of the project
        version (str): Version of the project
        message (str): Welcome message
        docs (str): URL to the documentation
        redocs (str): URL to the redoc documentation
        commitVersion (str): Commit version
    """

    projectName: str
    version: str
    message: str
    docs: str
    redocs: str
    commitVersion: str


class ModelBaseInfo(BaseModel):
    """
    Base model for all models

    Attributes:
        id (UUID): Unique identifier
        created_at (datetime): Created date
        updated_at (datetime): Updated date
    """

    id: UUID
    created_at: datetime
    updated_at: datetime


class FindBase(BaseModel):
    """
    Base model for search functionality

    Attributes:
        ordering (Optional[str]): Ordering parameter
        page (Optional[int]): Page number
        page_size (Optional[Union[int, str]]): Page size
    """

    ordering: Optional[str]
    page: Optional[int]
    page_size: Optional[Union[int, str]]


class SearchOptions(FindBase):
    """
    Model for search options

    Attributes:
        total_count (Optional[int]): Total count of results
    """

    total_count: Optional[int]


class FindResult(BaseModel):
    """
    Model for search results

    Attributes:
        items (Optional[List]): List of items
        search_options (Optional[SearchOptions]): Search options
    """

    items: Optional[List]
    search_options: Optional[SearchOptions]


class FindDateRange(BaseModel):
    """
    Model for date range search filters

    Attributes:
        created_at__lt (str): Less than filter for created date
        created_at__lte (str): Less than or equal filter for created date
        created_at__gt (str): Greater than filter for created date
        created_at__gte (str): Greater than or equal filter for created date
    """

    created_at__lt: str
    created_at__lte: str
    created_at__gt: str
    created_at__gte: str


class SuccesfullyCreated(BaseModel):
    """
    Model for successful creation response

    Attributes:
        message (Optional[str]): Success message
    """

    message: Optional[str] = "Successfully created"


class Blank(BaseModel):
    """A blank model used for various purposes."""

    pass

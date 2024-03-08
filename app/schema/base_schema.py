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

    Example:
        {
            "projectName": "Game API",
            "version": "0.1.0",
            "message": "Welcome to GAME API",
            "docs": "/docs",
            "redocs": "/redocs",
            "commitVersion": "c3f1e2a"
        }
    """
    projectName: str
    version: str
    message: str
    docs: str
    redocs: str
    commitVersion: str


class ModelBaseInfo(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


class FindBase(BaseModel):
    ordering: Optional[str]
    page: Optional[int]
    page_size: Optional[Union[int, str]]


class SearchOptions(FindBase):
    total_count: Optional[int]


class FindResult(BaseModel):
    items: Optional[List]
    search_options: Optional[SearchOptions]


class FindDateRange(BaseModel):
    created_at__lt: str
    created_at__lte: str
    created_at__gt: str
    created_at__gte: str


class SuccesfullyCreated(BaseModel):
    message: Optional[str] = "Successfully created"


class Blank(BaseModel):
    pass

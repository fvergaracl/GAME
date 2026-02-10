from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class RootEndpoint(BaseModel):
    """
    Public metadata payload returned by the API root endpoint.

    Attributes:
        projectName (str): Project name.
        version (str): Application version.
        message (str): Human-readable greeting/health message.
        docs (str): Relative or absolute URL to Swagger documentation.
        redocs (str): Relative or absolute URL to ReDoc documentation.
        commitVersion (str): Deployed git commit hash.
    """

    projectName: str = Field(
        ...,
        description="Project name exposed by the API.",
        example="GAME (Goals And Motivation Engine)",
    )
    version: str = Field(
        ...,
        description="Semantic version of the running backend.",
        example="1.4.2",
    )
    message: str = Field(
        ...,
        description="Welcome or status message of the API root endpoint.",
        example="Welcome to GAME API",
    )
    docs: str = Field(
        ...,
        description="Swagger UI documentation URL.",
        example="/docs",
    )
    redocs: str = Field(
        ...,
        description="ReDoc documentation URL.",
        example="/redocs",
    )
    commitVersion: str = Field(
        ...,
        description="Git commit hash of the deployed build.",
        example="7f9d8a3c2e4b1f0a9d6c5b4e3f2a1b0c9d8e7f6a",
    )


class ModelBaseInfo(BaseModel):
    """
    Shared metadata fields included in persisted resources.

    Attributes:
        id (UUID): Unique resource identifier.
        created_at (datetime): UTC creation timestamp.
        updated_at (datetime): UTC last update timestamp.
    """

    id: UUID = Field(
        ...,
        description="Unique identifier of the resource.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    created_at: datetime = Field(
        ...,
        description="UTC timestamp when the resource was created.",
        example="2026-02-10T12:15:00Z",
    )
    updated_at: datetime = Field(
        ...,
        description="UTC timestamp when the resource was last updated.",
        example="2026-02-10T12:45:00Z",
    )


class FindBase(BaseModel):
    """
    Common query options for pageable and sortable search endpoints.

    Attributes:
        ordering (Optional[str]): Sort expression (for example `-id`,
          `created_at`).
        page (Optional[int]): Page number in paginated responses.
        page_size (Optional[Union[int, str]]): Number of items per page, or a
          string sentinel when supported by the endpoint.
    """

    ordering: Optional[str] = Field(
        ...,
        description="Sort expression. Prefix with '-' for descending order.",
        example="-created_at",
    )
    page: Optional[int] = Field(
        ...,
        description="Page index (1-based) for paginated results.",
        example=1,
    )
    page_size: Optional[Union[int, str]] = Field(
        ...,
        description="Page size for pagination, or endpoint-specific string value.",
        example=10,
    )


class SearchOptions(FindBase):
    """
    Search metadata returned alongside collection results.

    Attributes:
        total_count (Optional[int]): Total number of records matching the
          applied filters.
    """

    total_count: Optional[int] = Field(
        ...,
        description="Total number of records available for the current filter set.",
        example=125,
    )


class FindResult(BaseModel):
    """
    Generic container for list endpoints with pagination metadata.

    Attributes:
        items (Optional[List]): Collection of result items.
        search_options (Optional[SearchOptions]): Paging/sorting metadata.
    """

    items: Optional[List] = Field(
        ...,
        description="List of resources returned by the query.",
        example=[],
    )
    search_options: Optional[SearchOptions] = Field(
        ...,
        description="Search metadata including ordering and pagination details.",
    )


class FindDateRange(BaseModel):
    """
    Date-range filter payload for created-at constraints.

    Attributes:
        created_at__lt (str): Strict upper bound for `created_at`.
        created_at__lte (str): Inclusive upper bound for `created_at`.
        created_at__gt (str): Strict lower bound for `created_at`.
        created_at__gte (str): Inclusive lower bound for `created_at`.
    """

    created_at__lt: str = Field(
        ...,
        description="Filter records with created_at earlier than this timestamp.",
        example="2026-02-11T00:00:00Z",
    )
    created_at__lte: str = Field(
        ...,
        description="Filter records with created_at earlier than or equal to this timestamp.",
        example="2026-02-11T23:59:59Z",
    )
    created_at__gt: str = Field(
        ...,
        description="Filter records with created_at later than this timestamp.",
        example="2026-02-01T00:00:00Z",
    )
    created_at__gte: str = Field(
        ...,
        description="Filter records with created_at later than or equal to this timestamp.",
        example="2026-02-01T00:00:00Z",
    )


class SuccesfullyCreated(BaseModel):
    """
    Standard response fragment for successful create operations.

    Attributes:
        message (Optional[str]): Human-readable success message.
    """

    message: Optional[str] = Field(
        default="Successfully created",
        description="Operation result message.",
        example="Successfully created",
    )


class Blank(BaseModel):
    """A blank model used for various purposes."""

    pass

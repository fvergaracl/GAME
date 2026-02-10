from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.schema.games_params_schema import (BaseFindGameParams, CreateGameParams,
                                            UpdateGameParams)
from app.schema.task_schema import TasksWithUsers
from app.util.schema import AllOptional


class BaseGame(BaseModel):
    """
    Base game payload.

    Attributes:
        platform (str): Platform identifier for the game context
          (for example: `web`, `mobile`).
    """

    platform: str = Field(
        ...,
        description="Platform where the game is configured to run.",
        example="web",
    )

    class Config:
        orm_mode = True


class BaseGameResult(BaseModel):
    """
    Canonical game representation returned by read endpoints.

    Attributes:
        gameId (UUID): Internal game identifier.
        created_at (Optional[datetime]): Resource creation timestamp (UTC).
        updated_at (Optional[datetime]): Last resource update timestamp (UTC).
        externalGameId (Optional[str]): Client-side game identifier.
        strategyId (Optional[str]): Strategy identifier bound to this game.
        platform (Optional[str]): Platform name.
        params (Optional[List[BaseFindGameParams]]): Effective game parameters.
    """

    gameId: UUID = Field(
        ...,
        description="Internal UUID of the game.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the game was created.",
        example="2026-02-10T12:15:00Z",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the game was last updated.",
        example="2026-02-10T12:45:00Z",
    )
    externalGameId: Optional[str] = Field(
        default=None,
        description="External identifier provided by the client system.",
        example="game-readme-001",
    )
    strategyId: Optional[str] = Field(
        default=None,
        description="Strategy id assigned to this game.",
        example="default",
    )
    platform: Optional[str] = Field(
        default=None,
        description="Target platform for the game.",
        example="web",
    )
    params: Optional[List[BaseFindGameParams]] = Field(
        default=None,
        description="Resolved game-level strategy parameters.",
    )

    class Config:
        orm_mode = True


class PostCreateGame(BaseModel):
    """
    Request schema for creating a game.

    Attributes:
        externalGameId (str): External game identifier in the client domain.
        platform (str): Target platform.
        strategyId (Optional[str]): Strategy identifier (`default` when omitted).
        params (Optional[List[CreateGameParams]]): Initial game parameters.
        apiKey_used (Optional[str]): API key used for request attribution.
        oauth_user_id (Optional[str]): OAuth subject used for request attribution.
    """

    externalGameId: str = Field(
        ...,
        description="External identifier of the game.",
        example="game-readme-001",
    )
    platform: str = Field(
        ...,
        description="Platform where the game operates.",
        example="web",
    )
    strategyId: Optional[str] = Field(
        default="default",
        description="Strategy identifier for scoring behavior.",
        example="default",
    )
    params: Optional[List[CreateGameParams]] = Field(
        default=None,
        description="Initial strategy/game parameters.",
        example=[CreateGameParams.example()],
    )
    apiKey_used: Optional[str] = Field(
        default=None,
        description="API key used by the caller when request is API-key based.",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )
    oauth_user_id: Optional[str] = Field(
        default=None,
        description="OAuth user subject that initiated the operation.",
        example="3c95c2d7-1ce8-4ea0-b35f-6dfd19127f35",
    )

    def example():
        return {
            "externalGameId": "game-readme-001",
            "platform": "web",
            "strategyId": "default",
            "params": [{"key": "variable_basic_points", "value": 10}],
        }


class PatchGame(BaseModel):
    """
    Request schema for partial game updates.

    Attributes:
        externalGameId (Optional[str]): External game identifier.
        strategyId (Optional[str]): Strategy identifier.
        platform (Optional[str]): Platform name.
        params (Optional[List[UpdateGameParams]]): Updated game parameters.
    """

    externalGameId: Optional[str] = Field(
        default=None,
        description="External identifier of the game.",
        example="game-readme-001-updated",
    )
    strategyId: Optional[str] = Field(
        default=None,
        description="Updated strategy id.",
        example="default",
    )
    platform: Optional[str] = Field(
        default=None,
        description="Updated platform value.",
        example="mobile",
    )
    params: Optional[List[UpdateGameParams]] = Field(
        default=None,
        description="Updated game parameters.",
    )


class GameCreated(BaseGameResult):
    """
    Response schema returned after successful game creation.

    Attributes:
        message (Optional[str]): Operation success message.
    """

    message: Optional[str] = Field(
        default="Successfully created",
        description="Human-readable operation result message.",
        example="Successfully created",
    )


class ResponsePatchGame(PatchGame):
    """
    Response schema returned after successful game update.

    Attributes:
        message (Optional[str]): Operation success message.
    """

    message: Optional[str] = Field(
        default="Successfully updated",
        description="Human-readable operation result message.",
        example="Successfully updated",
    )


class FindGameById(ModelBaseInfo):
    """
    Detailed game schema resolved by internal `gameId`.

    Attributes:
        externalGameId (Optional[str]): External game identifier.
        platform (Optional[str]): Platform name.
        params (Optional[List[UpdateGameParams]]): Game parameters.
    """

    externalGameId: Optional[str] = Field(
        default=None,
        description="External game identifier.",
        example="game-readme-001",
    )
    platform: Optional[str] = Field(
        default=None,
        description="Platform associated with the game.",
        example="web",
    )
    params: Optional[List[UpdateGameParams]] = Field(
        default=None,
        description="Game parameters and values.",
    )


class PostFindGame(FindBase, BaseGame, metaclass=AllOptional):
    """
    Query schema for listing/filtering games.

    Inherits:
    - pagination/sort options from `FindBase`
    - platform filter from `BaseGame`
    """

    externalGameId: Optional[str] = Field(
        default=None,
        description="Optional external game identifier filter.",
        example="game-readme-001",
    )


class FindGameResult(BaseModel):
    """
    Collection response for game search operations.

    Attributes:
        items (Optional[List[BaseGameResult]]): Result set of games.
        search_options (Optional[SearchOptions]): Pagination/search metadata.
    """

    items: Optional[List[BaseGameResult]] = Field(
        default=None,
        description="List of games returned by the query.",
    )
    search_options: Optional[SearchOptions] = Field(
        default=None,
        description="Pagination and ordering metadata.",
    )


class ListTasksWithUsers(BaseModel):
    """
    Response schema for users grouped by task within a game.

    Attributes:
        gameId (UUID): Internal game identifier.
        tasks (List[TasksWithUsers]): Tasks and associated users.
    """

    gameId: UUID = Field(
        ...,
        description="Internal UUID of the game.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    tasks: List[TasksWithUsers] = Field(
        ...,
        description="Task list with users that have activity in each task.",
    )

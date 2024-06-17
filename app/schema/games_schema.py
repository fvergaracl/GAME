from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schema.base_schema import FindBase, ModelBaseInfo, SearchOptions
from app.schema.games_params_schema import (BaseFindGameParams,
                                            CreateGameParams, UpdateGameParams)
from app.schema.task_schema import TasksWithUsers
from app.util.schema import AllOptional


class BaseGame(BaseModel):
    """
    Base model for a game

    Attributes:
        platform (str): Platform name
    """

    platform: str

    class Config:
        orm_mode = True


class BaseGameResult(BaseModel):
    """
    Model for game result

    Attributes:
        gameId (UUID): Game ID
        created_at (Optional[datetime]): Created date
        updated_at (Optional[datetime]): Updated date
        externalGameId (Optional[str]): External game ID
        strategyId (Optional[str]): Strategy ID
        platform (Optional[str]): Platform name
        params (Optional[List[BaseFindGameParams]]): Game parameters
    """

    gameId: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    externalGameId: Optional[str] = None
    strategyId: Optional[str] = None
    platform: Optional[str] = None
    params: Optional[List[BaseFindGameParams]] = None

    class Config:
        orm_mode = True


class PostCreateGame(BaseModel):
    """
    Model for creating a game

    Attributes:
        externalGameId (str): External game ID
        platform (str): Platform name
        strategyId (Optional[str]): Strategy ID
        params (Optional[List[CreateGameParams]]): Game parameters
    """

    externalGameId: str
    platform: str
    strategyId: Optional[str] = "default"
    params: Optional[List[CreateGameParams]]

    def example():
        return {
            "externalGameId": "string",
            "platform": "string",
            "strategyId": "default",
            "params": [{"key": "variable_basic_points", "value": 10}],
        }


class PatchGame(BaseModel):
    """
    Model for updating a game

    Attributes:
        externalGameId (Optional[str]): External game ID
        strategyId (Optional[str]): Strategy ID
        platform (Optional[str]): Platform name
        params (Optional[List[UpdateGameParams]]): Game parameters
    """

    externalGameId: Optional[str]
    strategyId: Optional[str]
    platform: Optional[str]
    params: Optional[List[UpdateGameParams]]


class GameCreated(BaseGameResult):
    """
    Model for game creation response

    Attributes:
        message (Optional[str]): Success message
    """

    message: Optional[str] = "Successfully created"


class ResponsePatchGame(PatchGame):
    """
    Model for game update response

    Attributes:
        message (Optional[str]): Success message
    """

    message: Optional[str] = "Successfully updated"


class FindGameById(ModelBaseInfo):
    """
    Model for finding a game by ID

    Attributes:
        externalGameId (Optional[str]): External game ID
        platform (Optional[str]): Platform name
        params (Optional[List[UpdateGameParams]]): Game parameters
    """

    externalGameId: Optional[str]
    platform: Optional[str]
    params: Optional[List[UpdateGameParams]]


class PostFindGame(FindBase, BaseGame, metaclass=AllOptional):
    """
    Model for finding a game

    Inherits attributes from FindBase and BaseGame.
    """

    ...


class FindGameResult(BaseModel):
    """
    Model for game search results

    Attributes:
        items (Optional[List[BaseGameResult]]): List of game results
        search_options (Optional[SearchOptions]): Search options
    """

    items: Optional[List[BaseGameResult]]
    search_options: Optional[SearchOptions]


class ListTasksWithUsers(BaseModel):
    """
    Model for listing tasks with users

    Attributes:
        gameId (UUID): Game ID
        tasks (List[TasksWithUsers]): List of tasks with users
    """

    gameId: UUID
    tasks: List[TasksWithUsers]

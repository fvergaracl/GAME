from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schema.base_schema import (FindBase, ModelBaseInfo, SearchOptions,
                                    SuccesfullyCreated)
from app.schema.games_params_schema import CreateGameParams
from app.schema.strategy_schema import Strategy
from app.schema.tasks_params_schema import CreateTaskParams
from app.util.schema import AllOptional


class BaseTask(BaseModel):
    """
    Base task identifier payload.

    Attributes:
        externalTaskId (str): External task identifier.
        gameId (UUID): Internal game identifier.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-login",
    )
    gameId: UUID = Field(
        ...,
        description="Internal UUID of the game.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )


class AsignPointsToExternalUserId(BaseModel):
    """
    Request schema for assigning points to a user by external id in a task.

    Attributes:
        externalUserId (str): External user identifier.
        data (Optional[dict]): Additional metadata consumed by scoring logic.
        isSimulated (Optional[bool]): Whether to run assignment in simulation mode.
    """

    externalUserId: str = Field(
        ...,
        description="External user identifier.",
        example="user-123",
    )
    data: Optional[dict] = Field(
        default=None,
        description="Context payload for scoring strategy evaluation.",
        example={"event": "task_completed", "source": "mobile-app"},
    )
    isSimulated: Optional[bool] = Field(
        default=False,
        description="If true, executes simulation logic when available.",
        example=False,
    )


class CreateTaskPost(BaseModel):
    """
    Request schema for creating a single task in a game.

    Attributes:
        externalTaskId (str): External task identifier.
        strategyId (Optional[str]): Strategy identifier to apply on this task.
        params (Optional[List[CreateTaskParams]]): Task-level strategy parameters.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-login",
    )
    strategyId: Optional[str] = Field(
        default=None,
        description="Optional strategy id for this specific task.",
        example="default",
    )
    params: Optional[List[CreateTaskParams]] = Field(
        default=None,
        description="Task-specific parameters that override/extend game settings.",
        example=[CreateTaskParams.example()],
    )

    def example():
        return {
            "externalTaskId": "string",
            "strategyId": "default",
            "params": [CreateTaskParams.example()],
        }


class CreateTasksPost(BaseModel):
    """
    Request schema for bulk task creation.

    Attributes:
        tasks (List[CreateTaskPost]): List of task creation payloads.
    """

    tasks: List[CreateTaskPost] = Field(
        ...,
        description="Tasks to be created in bulk.",
    )

    def example():
        return {
            "tasks": [CreateTaskPost.example()],
            "strategyId": "default",
            "params": [CreateTaskParams.example()],
        }


class PostFindTask(FindBase, metaclass=AllOptional):  # noqa
    """
    Query schema for task search/listing operations.

    Inherits ordering/pagination fields from `FindBase`.
    """

    ...


class FoundTask(ModelBaseInfo):
    """
    Task representation returned by search/detail endpoints.

    Attributes:
        externalTaskId (str): External task identifier.
        gameParams (Optional[List[CreateGameParams]]): Resolved game parameters.
        taskParams (Optional[List[CreateTaskParams]]): Resolved task parameters.
        strategy (Optional[Strategy]): Strategy definition applied to the task.
    """

    externalTaskId: str = Field(
        ...,
        description="External task identifier.",
        example="task-login",
    )
    gameParams: Optional[List[CreateGameParams]] = Field(
        default=None,
        description="Game-level parameters effective for this task.",
    )
    taskParams: Optional[List[CreateTaskParams]] = Field(
        default=None,
        description="Task-level parameters configured for this task.",
    )
    strategy: Optional[Strategy] = Field(
        default=None,
        description="Strategy bound to this task.",
    )


class FoundTasks(BaseModel):
    """
    Collection response for task search results.

    Attributes:
        items (Optional[List[FoundTask]]): List of matched tasks.
        search_options (Optional[SearchOptions]): Pagination/search metadata.
    """

    items: Optional[List[FoundTask]] = Field(
        default=None,
        description="Tasks returned by the query.",
    )
    search_options: Optional[SearchOptions] = Field(
        default=None,
        description="Search metadata for pagination and ordering.",
    )


class CreateTask(CreateTaskPost, metaclass=AllOptional):
    """
    Internal task creation schema enriched with ownership metadata.

    Attributes:
        gameId (str): Internal game identifier.
        apiKey_used (Optional[str]): API key used in the originating request.
    """

    gameId: str
    apiKey_used: Optional[str]


class FindTask(FindBase, metaclass=AllOptional):
    """
    Query schema for task lookup by game context.

    Attributes:
        gameId (UUID): Internal game identifier filter.
    """

    gameId: UUID


class CreateTaskPostSuccesfullyCreated(SuccesfullyCreated):
    """
    Response schema returned for successfully created tasks.

    Attributes:
        externalTaskId (str): External task identifier.
        externalGameId (str): External game identifier.
        gameParams (Optional[List[CreateGameParams]]): Effective game parameters.
        taskParams (Optional[List[CreateTaskParams]]): Effective task parameters.
        strategy (Optional[Strategy]): Strategy assigned to the task.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the created task.",
        example="task-login",
    )
    externalGameId: str = Field(
        ...,
        description="External identifier of the owning game.",
        example="game-readme-001",
    )
    gameParams: Optional[List[CreateGameParams]] = Field(
        default=None,
        description="Game-level parameters applied to the task context.",
    )
    taskParams: Optional[List[CreateTaskParams]] = Field(
        default=None,
        description="Task-level parameters persisted for the created task.",
    )
    strategy: Optional[Strategy] = Field(
        default=None,
        description="Strategy resolved for the created task.",
    )


class CreateTaskPostError(BaseModel):
    """
    Error entry for a failed task creation in bulk operations.

    Attributes:
        task (CreateTaskPost): Original task payload that failed.
        error (str): Error message describing the failure reason.
    """

    task: CreateTaskPost = Field(
        ...,
        description="Original task payload that could not be created.",
    )
    error: str = Field(
        ...,
        description="Failure reason for this task creation attempt.",
        example="Task already exists with externalTaskId: task-login",
    )


class CreateTasksPostBulkCreated(BaseModel):
    """
    Bulk task creation response partitioned by success and failure.

    Attributes:
        succesfully_created (List[CreateTaskPostSuccesfullyCreated]): List of
          successfully created tasks.
        failed_to_create (List[CreateTaskPostError]): List of tasks that
          failed to be created.
    """

    succesfully_created: List[CreateTaskPostSuccesfullyCreated] = Field(
        ...,
        description="Tasks successfully created during the bulk request.",
    )
    failed_to_create: List[CreateTaskPostError] = Field(
        ...,
        description="Tasks that failed to be created with error details.",
    )


class AddActionDidByUserInTask(BaseModel):
    """
    Request schema to register an action performed by a user in a task.

    This payload is used by:
    - `POST /games/{gameId}/tasks/{externalTaskId}/action`

    Note:
    - `gameId` and `externalTaskId` are provided in the URL path, not in this
      body.

    Attributes:
        typeAction (str): Canonical action/event identifier
          (for example: `TASK_COMPLETED`, `LOGIN`, `CLICK`).
        data (dict): Structured metadata associated with the action. Must be
          JSON-serializable.
        description (str): Human-readable explanation of the event.
        externalUserId (str): External identifier of the user who triggered
          the action.
    """

    typeAction: str = Field(
        ...,
        description="Canonical action/event identifier.",
        example="TASK_COMPLETED",
    )
    data: dict = Field(
        ...,
        description="Action metadata payload (JSON object).",
        example={"source": "mobile-app", "durationSeconds": 84},
    )
    description: str = Field(
        ...,
        description="Human-readable description of the action.",
        example="User completed the task from the mobile app.",
    )
    externalUserId: str = Field(
        ...,
        description="External user identifier that triggered the action.",
        example="user-123",
    )

    def example():
        return {
            "typeAction": "TASK_COMPLETED",
            "data": {"source": "mobile-app", "durationSeconds": 84},
            "description": "User completed the task from the mobile app.",
            "externalUserId": "user-123",
        }


class ResponseAddActionDidByUserInTask(ModelBaseInfo, AddActionDidByUserInTask):
    """
    Response schema for a persisted user action in a task context.

    Includes all action fields from `AddActionDidByUserInTask` plus metadata
    inherited from `ModelBaseInfo`.
    """

    message: Optional[str] = Field(
        default=None,
        description="Operation result message.",
        example="Action added successfully",
    )
    ...


class AssignedPointsToExternalUserId(BaseModel):
    """
    Response schema for points assigned to a user in a task.

    Attributes:
        points (int): Points assigned.
        caseName (str): Strategy case/rule that generated the points.
        isACreatedUser (bool): Indicates if the user was auto-created.
        gameId (UUID): Internal game identifier.
        externalTaskId (str): External task identifier.
        created_at (str): Creation timestamp of the points record.
    """

    points: int = Field(
        ...,
        description="Points assigned to the user for the task event.",
        example=20,
    )
    caseName: str = Field(
        ...,
        description="Strategy case/rule name applied to compute points.",
        example="variable_basic_points",
    )
    isACreatedUser: bool = Field(
        ...,
        description="Whether the target user was auto-created during assignment.",
        example=False,
    )
    gameId: UUID = Field(
        ...,
        description="Internal UUID of the game.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-login",
    )
    created_at: str = Field(
        ...,
        description="UTC timestamp when the points record was created.",
        example="2026-02-10T12:30:00Z",
    )


class SimulatedTaskPoints(BaseModel):
    """
    Simulated scoring result for a single task/user pair.

    Attributes:
        externalUserId (str): External user identifier.
        externalTaskId (str): External task identifier.
        userGroup (Optional[str]): Assigned simulation/control group.
        dimensions (List[dict]): Dimension-level simulation details.
        totalSimulatedPoints (int): Total simulated points for the task.
        expirationDate (str): Expiration timestamp for this simulation result.
    """

    externalUserId: str = Field(
        ...,
        description="External identifier of the simulated user.",
        example="user-123",
    )
    externalTaskId: str = Field(
        ...,
        description="External identifier of the simulated task.",
        example="task-login",
    )
    userGroup: Optional[str] = Field(
        default=None,
        description="Assigned group for simulation/control logic.",
        example="control",
    )
    dimensions: List[dict] = Field(
        ...,
        description="Dimension-level breakdown used in simulation calculation.",
        example=[{"name": "engagement", "value": 0.74}],
    )
    totalSimulatedPoints: int = Field(
        ...,
        description="Total simulated points for this task.",
        example=42,
    )
    expirationDate: str = Field(
        ...,
        description="UTC expiration timestamp of the simulation payload.",
        example="2026-02-10T18:30:00Z",
    )


class SimulatedPointsAssignedToUser(BaseModel):
    """
    Container schema for all simulated task-point outputs for a user.

    Attributes:
        simulationHash (str): Hash fingerprint of simulation inputs/outputs.
        tasks (List[SimulatedTaskPoints]): Simulated points by task.
    """

    simulationHash: str = Field(
        ...,
        description="Hash that uniquely identifies the simulation payload.",
        example="8e9fc0f2ef79ed3fca6053a5932f7a6d8f3f3f77b2437d2b7d8ea59e21a4fd4e",
    )
    tasks: List[SimulatedTaskPoints] = Field(
        ...,
        description="List of simulated task-point results.",
    )


class TaskPointsResponseByUser(BaseTask):
    """
    Task points response scoped to one user.

    Attributes:
        taskId (str): Internal task identifier.
        externalTaskId (str): External task identifier.
        gameId (str): Internal game identifier.
        points (Optional[int]): Aggregated points for the user-task pair.
    """

    taskId: str = Field(
        ...,
        description="Internal UUID of the task (serialized as string).",
        example="2a18d9a9-8eb5-4d33-a7bd-9590ea7ea41e",
    )
    externalTaskId: str = Field(
        ...,
        description="External task identifier.",
        example="task-login",
    )
    gameId: str = Field(
        ...,
        description="Internal UUID of the game (serialized as string).",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    points: Optional[int] = Field(
        default=None,
        description="Total points associated with this user-task relation.",
        example=120,
    )


class BaseUser(BaseModel):
    """
    Base user identity fragment used in task-user responses.

    Attributes:
        externalUserId (str): External user identifier.
        created_at (Optional[str]): UTC timestamp when user was created.
    """

    externalUserId: str = Field(
        ...,
        description="External identifier of the user.",
        example="user-123",
    )
    created_at: Optional[str] = Field(
        default=None,
        description="UTC timestamp when the user was created.",
        example="2026-02-10T12:20:00Z",
    )


class BaseUserFirstAction(BaseUser):
    """
    User projection including first action timestamp.

    Attributes:
        firstAction (Optional[str]): Timestamp of the first task action/points event.
    """

    firstAction: Optional[str] = Field(
        default=None,
        description="UTC timestamp of the user's first action in the task context.",
        example="2026-02-10T12:30:00Z",
    )


class TasksWithUsers(BaseModel):
    """
    Task projection including users that interacted with it.

    Attributes:
        externalTaskId (str): External task identifier.
        users (List[BaseUserFirstAction]): Users with activity in this task.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-login",
    )
    users: List[BaseUserFirstAction] = Field(
        ...,
        description="List of users associated with this task activity.",
    )

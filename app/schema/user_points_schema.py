from typing import List, Optional

from pydantic import BaseModel, Field

from app.schema.base_schema import ModelBaseInfo
from app.schema.wallet_schema import WalletWithoutUserId
from app.util.schema import AllOptional


class PostAssignPointsToUser(BaseModel):
    """
    Request schema for assigning points to a user in a task context.

    Attributes:
        taskId (str): Internal UUID of the task (serialized as string).
        caseName (Optional[str]): Incentive/scoring case label.
        points (Optional[int]): Number of points to grant.
        description (Optional[str]): Human-readable assignment reason.
        data (Optional[dict]): Additional structured metadata for tracing/audit.
    """

    taskId: str = Field(
        ...,
        description="Internal UUID of the task that generated this points assignment.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    caseName: Optional[str] = Field(
        default=None,
        description="Scoring case/category used by the strategy engine.",
        example="TASK_COMPLETION",
    )
    points: Optional[int] = Field(
        default=None,
        description="Points to assign. Use positive values for rewards and negative values only if allowed by business rules.",
        example=25,
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of why the points were assigned.",
        example="User completed task before deadline.",
    )
    data: Optional[dict] = Field(
        default=None,
        description="Arbitrary metadata attached to the assignment for diagnostics and analytics.",
        example={"source": "mobile-app", "attempt": 1},
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative points-assignment payload.
        """
        return {
            "taskId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
            "caseName": "TASK_COMPLETION",
            "points": 25,
            "description": "User completed task before deadline.",
            "data": {"source": "mobile-app", "attempt": 1},
        }


class PointsAssigned(BaseModel):
    """
    Aggregate schema representing assigned points and award count.

    Attributes:
        points (int): Total points assigned in the queried context.
        timesAwarded (int): Number of award events contributing to `points`.
    """

    points: int = Field(
        ...,
        description="Total points assigned in the current aggregation scope.",
        example=120,
    )
    timesAwarded: int = Field(
        ...,
        description="Number of times points were awarded.",
        example=6,
    )


class PointsData(BaseModel):
    """
    Detail record for a single points assignment event.

    Attributes:
        points (int): Points assigned in this event.
        caseName (str): Case/category applied to this event.
        created_at (str): Event timestamp in ISO-8601 format.
    """

    points: int = Field(
        ...,
        description="Points assigned in this single event.",
        example=15,
    )
    caseName: str = Field(
        ...,
        description="Case/category associated with this assignment event.",
        example="TASK_COMPLETION",
    )
    created_at: str = Field(
        ...,
        description="Timestamp when points were created (ISO-8601 UTC string).",
        example="2026-02-10T12:20:00Z",
    )


class PointsAssignedToUser(PointsAssigned):
    """
    Aggregate points assigned to a specific external user.

    Attributes:
        externalUserId (str): Consumer-facing user identifier.
    """

    externalUserId: str = Field(
        ...,
        description="External user identifier associated with the awarded points.",
        example="user-12345",
    )


class PointsAssignedToUserDetails(PointsAssignedToUser):
    """
    Detailed aggregate points assigned to an external user.

    Attributes:
        pointsData (Optional[List[PointsData]]): Per-event assignment details.
    """

    pointsData: Optional[List[PointsData]] = Field(
        default=None,
        description="Detailed list of assignment events for this user and scope.",
        example=[
            {
                "points": 15,
                "caseName": "TASK_COMPLETION",
                "created_at": "2026-02-10T12:20:00Z",
            }
        ],
    )


class TaskPointsByGame(BaseModel):
    """
    Points aggregation for one task inside a game.

    Attributes:
        externalTaskId (str): Consumer-facing task identifier.
        points (List[PointsAssignedToUser]): Aggregated points by user.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-daily-walk",
    )
    points: List[PointsAssignedToUser] = Field(
        ...,
        description="Aggregated points grouped by user for this task.",
    )


class TaskPointsByGameWithDetails(BaseModel):
    """
    Detailed points aggregation for one task inside a game.

    Attributes:
        externalTaskId (str): Consumer-facing task identifier.
        points (List[PointsAssignedToUserDetails]): Detailed points by user.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-daily-walk",
    )
    points: List[PointsAssignedToUserDetails] = Field(
        ...,
        description="Detailed aggregated points grouped by user for this task.",
    )


class AllPointsByGame(BaseModel):
    """
    Aggregated points view for an entire game.

    Attributes:
        externalGameId (str): Consumer-facing game identifier.
        created_at (str): Snapshot creation timestamp.
        task (List[TaskPointsByGame]): Aggregated task-level points.
    """

    externalGameId: str = Field(
        ...,
        description="External identifier of the game.",
        example="game-city-mobility",
    )
    created_at: str = Field(
        ...,
        description="Timestamp when this points snapshot was produced.",
        example="2026-02-10T12:20:00Z",
    )
    task: List[TaskPointsByGame] = Field(
        ...,
        description="Task-level points aggregation for this game.",
    )


class AllPointsByGameWithDetails(BaseModel):
    """
    Detailed aggregated points view for an entire game.

    Attributes:
        externalGameId (str): Consumer-facing game identifier.
        created_at (str): Snapshot creation timestamp.
        task (List[TaskPointsByGameWithDetails]): Detailed task-level points.
    """

    externalGameId: str = Field(
        ...,
        description="External identifier of the game.",
        example="game-city-mobility",
    )
    created_at: str = Field(
        ...,
        description="Timestamp when this points snapshot was produced.",
        example="2026-02-10T12:20:00Z",
    )
    task: List[TaskPointsByGameWithDetails] = Field(
        ...,
        description="Detailed task-level points aggregation for this game.",
    )


class AllPointsByGameWithDetails(BaseModel):
    """
    Detailed aggregated points view for an entire game.

    Attributes:
        externalGameId (str): Consumer-facing game identifier.
        created_at (str): Snapshot creation timestamp.
        task (List[TaskPointsByGameWithDetails]): Detailed task-level points.
    """

    externalGameId: str = Field(
        ...,
        description="External identifier of the game.",
        example="game-city-mobility",
    )
    created_at: str = Field(
        ...,
        description="Timestamp when this points snapshot was produced.",
        example="2026-02-10T12:20:00Z",
    )
    task: List[TaskPointsByGameWithDetails] = Field(
        ...,
        description="Detailed task-level points aggregation for this game.",
    )


class BaseUserPointsBaseModel(PostAssignPointsToUser):
    """
    Internal base schema for points assignment tied to an internal user.

    Attributes:
        userId (str): Internal UUID of the user (serialized as string).
    """

    userId: str = Field(
        ...,
        description="Internal UUID of the user receiving the points.",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )


class BaseUserPointsBaseModelWithCaseName(BaseUserPointsBaseModel):
    """
    Internal points schema variant that explicitly exposes `caseName`.

    Attributes:
        caseName (Optional[str]): Incentive/scoring case label.
    """

    caseName: Optional[str] = Field(
        default=None,
        description="Scoring case/category used by the strategy engine.",
        example="TASK_COMPLETION",
    )


class UserPointsAssign(BaseUserPointsBaseModel):
    """
    Request schema for assigning points, including API key provenance.

    Attributes:
        apiKey_used (Optional[str]): API key used by the caller (if applicable).
    """

    apiKey_used: Optional[str] = Field(
        default=None,
        description="API key used for the request (when API-key auth is used).",
        example="gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
    )

    @staticmethod
    def example() -> dict:
        """
        Returns a representative user-points assignment payload.
        """
        return {
            "userId": "8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
            "taskId": "4ce32be2-77f6-4ffc-8e07-78dc220f0520",
            "caseName": "TASK_COMPLETION",
            "points": 25,
            "description": "User completed task before deadline.",
            "data": {"source": "mobile-app", "attempt": 1},
            "apiKey_used": "gk_live_3f6a9e0f1a2b4c5d6e7f8a9b",
        }


class UserPointsAssigned(ModelBaseInfo, BaseUserPointsBaseModel):
    """
    Response schema returned after a successful points assignment.

    Attributes:
        userId (str): Internal user identifier.
        taskId (str): Internal task identifier.
        wallet (Optional[WalletWithoutUserId]): Updated wallet snapshot.
        description (Optional[str]): Assignment description.
        message (Optional[str]): Operation result message.
    """

    userId: str = Field(
        ...,
        description="Internal UUID of the user receiving points.",
        example="8f9d6bc1-2b5f-4cab-b82a-2b0e61bf7c1d",
    )
    taskId: str = Field(
        ...,
        description="Internal UUID of the task generating points.",
        example="4ce32be2-77f6-4ffc-8e07-78dc220f0520",
    )
    wallet: Optional[WalletWithoutUserId] = Field(
        default=None,
        description="Wallet state after the points assignment.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable reason for the assignment.",
        example="User completed task before deadline.",
    )
    message: Optional[str] = Field(
        default="Successfully assigned",
        description="Operation result message.",
        example="Successfully assigned",
    )


class UserPoints(ModelBaseInfo, BaseUserPointsBaseModel, metaclass=AllOptional):
    """
    Persisted user points record schema.

    All fields inherited from base models can be treated as optional in
    partial update scenarios due to the `AllOptional` metaclass.
    """

    ...


class ResponseGetPointsByTask(BaseModel):
    """
    Response schema for points grouped by task and user.

    Attributes:
        externalUserId (str): Consumer-facing user identifier.
        points (int): Total points for the user in the task scope.
    """

    externalUserId: str = Field(
        ...,
        description="External user identifier.",
        example="user-12345",
    )
    points: int = Field(
        ...,
        description="Total points for this user in the queried task.",
        example=95,
    )


class PointsDetail(BaseModel):
    """
    Detailed points entry for a task timeline.

    Attributes:
        points (int): Points awarded in the event.
        caseName (str): Case/category associated with the event.
        created_at (str): Event timestamp in ISO-8601 format.
    """

    points: int = Field(
        ...,
        description="Points awarded in this detailed event entry.",
        example=10,
    )
    caseName: str = Field(
        ...,
        description="Case/category used for this award event.",
        example="BONUS_STREAK",
    )
    created_at: str = Field(
        ...,
        description="Timestamp when the points were created (ISO-8601 UTC string).",
        example="2026-02-10T12:20:00Z",
    )


class TaskDetail(BaseModel):
    """
    Detailed points timeline for one external task.

    Attributes:
        externalTaskId (str): Consumer-facing task identifier.
        pointsData (List[PointsDetail]): Detailed points events for the task.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-daily-walk",
    )
    pointsData: List[PointsDetail] = Field(
        ...,
        description="Detailed points entries recorded for this task.",
    )


class GameDetail(BaseModel):
    """
    Detailed points aggregation for one game in a user-centric response.

    Attributes:
        externalGameId (str): Consumer-facing game identifier.
        points (int): Total points within this game.
        timesAwarded (int): Number of award events within this game.
        tasks (List[TaskDetail]): Task-level detailed breakdown.
    """

    externalGameId: str = Field(
        ...,
        description="External identifier of the game.",
        example="game-city-mobility",
    )
    points: int = Field(
        ...,
        description="Total points accumulated in this game.",
        example=340,
    )
    timesAwarded: int = Field(
        ...,
        description="Number of award events in this game.",
        example=18,
    )
    tasks: List[TaskDetail] = Field(
        ...,
        description="Task-level detailed points for this game.",
    )


class UserGamePoints(BaseModel):
    """
    User-centric points aggregation across games.

    Attributes:
        externalUserId (str): Consumer-facing user identifier.
        points (int): Total points across the selected scope.
        timesAwarded (int): Number of award events in the selected scope.
        games (List[GameDetail]): Detailed per-game breakdown.
        userExists (Optional[bool]): Indicates if user exists in the platform.
    """

    externalUserId: str = Field(
        ...,
        description="External user identifier.",
        example="user-12345",
    )
    points: int = Field(
        ...,
        description="Total points accumulated by the user in the query scope.",
        example=500,
    )
    timesAwarded: int = Field(
        ...,
        description="Number of award events for the user in the query scope.",
        example=30,
    )
    games: List[GameDetail] = Field(
        ...,
        description="Detailed game-level points breakdown for the user.",
    )
    userExists: Optional[bool] = Field(
        default=True,
        description="Whether the external user exists in the platform context.",
        example=True,
    )


class ResponseGetPointsByGame(BaseModel):
    """
    Response schema for points grouped by task inside a game.

    Attributes:
        externalTaskId (str): Consumer-facing task identifier.
        points (List[ResponseGetPointsByTask]): Per-user points for the task.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-daily-walk",
    )
    points: List[ResponseGetPointsByTask] = Field(
        ...,
        description="Per-user points entries for this task.",
    )


class PointsByUserInTask(BaseModel):
    """
    Points summary for one user within a specific external task.

    Attributes:
        externalTaskId (str): Consumer-facing task identifier.
        points (int): User points in this task.
    """

    externalTaskId: str = Field(
        ...,
        description="External identifier of the task.",
        example="task-daily-walk",
    )
    points: int = Field(
        ...,
        description="Total points earned by the user for this task.",
        example=80,
    )


class ResponsePointsByExternalUserId(BaseModel):
    """
    Response schema for points summary by external user identifier.

    Attributes:
        externalUserId (str): Consumer-facing user identifier.
        points (int): Total points in the selected scope.
        points_by_task (List[PointsByUserInTask]): Task-level points breakdown.
    """

    externalUserId: str = Field(
        ...,
        description="External user identifier.",
        example="user-12345",
    )
    points: int = Field(
        ...,
        description="Total points accumulated by the user.",
        example=210,
    )
    points_by_task: List[PointsByUserInTask] = Field(
        ...,
        description="Task-level points breakdown for the user.",
    )

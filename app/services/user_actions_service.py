from app.core.exceptions import GoneError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_actions_repository import UserActionsRepository
from app.repository.user_repository import UserRepository
from app.schema.task_schema import (
    AddActionDidByUserInTask, ResponseAddActionDidByUserInTask
)
from app.services.base_service import BaseService
from app.schema.user_actions_schema import CreateUserActions


class UserActionsService(BaseService):
    """
    Service class for managing user points.

    Attributes:
        user_points_repository (UserPointsRepository): Repository instance for
          user points.
        users_repository (UserRepository): Repository instance for users.
        game_repository (GameRepository): Repository instance for games.
        task_repository (TaskRepository): Repository instance for tasks.
        wallet_repository (WalletRepository): Repository instance for wallets.
        wallet_transaction_repository (WalletTransactionRepository):
          Repository instance for wallet transactions.
        strategy_service (StrategyService): Service instance for strategies.
    """

    def __init__(
        self,
        user_actions_repository: UserActionsRepository,
        users_repository: UserRepository,
        game_repository: GameRepository,
        task_repository: TaskRepository,
    ):
        """
        Initializes the UserPointsService with the provided repositories and
          services.

        Args:
            user_actions_repository: The user points repository instance.
            users_repository: The user repository instance.
            game_repository: The game repository instance.
            task_repository: The task repository instance.
        """
        self.user_actions_repository = user_actions_repository
        self.users_repository = users_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        super().__init__(user_actions_repository)

    def user_add_action_in_task(
        # action is JSON object
        self,
        externalTaskId: str,
        action: AddActionDidByUserInTask,
    ):
        """
        Add action in task for user.

        Args:
            user_id (UUID): The user ID.
            task_id (UUID): The task ID.
            action (str): The action.

        Returns:
            object: The added action in task for user.

        Raises:
            NotFoundError: If the user or task is not found.
            GoneError: If the task is not active.
        """
        user = self.users_repository.read_by_column(
            "externalUserId",
            action.externalUserId,
            not_found_raise_exception=False,
        )
        if user is None:
            user = self.users_repository.create_user_by_externalUserId(
                externalUserId=action.externalUserId
            )
        task = self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message=(
                f"Task not found (externalTaskId) : {externalTaskId}"
            ),
        )

        if task.status != "open":
            raise GoneError("Task is not active")

        new_action = CreateUserActions(
            typeAction=action.typeAction,
            data=action.data,
            description=action.description,
            userId=str(user.id),
        )
        created_action = self.user_actions_repository.create(new_action)
        response = ResponseAddActionDidByUserInTask(
            **created_action.dict(),
            externalUserId=str(action.externalUserId),
            message="Action added successfully",
        )
        return response

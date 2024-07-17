from uuid import UUID
from app.services.strategy_service import StrategyService
from app.services.base_service import BaseService
from app.schema.task_schema import AddActionDidByUserInTask
from app.core.exceptions import NotFoundError, GoneError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_actions_repository import UserActionsRepository
from app.repository.user_repository import UserRepository


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
            users_actions_repository: UserActionsRepository,
            users_repository: UserRepository,
            game_repository: GameRepository,
            task_repository: TaskRepository,
    ):
        """
        Initializes the UserPointsService with the provided repositories and
          services.

        Args:
            users_actions_repository: The user points repository instance.
            users_repository: The user repository instance.
            game_repository: The game repository instance.
            task_repository: The task repository instance.
            strategy_service: The strategy service instance.
        """
        self.users_actions_repository = users_actions_repository
        self.users_repository = users_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        self.strategy_service = StrategyService()
        super().__init__(users_actions_repository)

    def user_add_action_in_task(
            # action is JSON object
            self, gameId: UUID, externalTaskId: str,
            action: AddActionDidByUserInTask
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
        user = self.users_repository.read_by_id(
            action.userId,
            not_found_message=f"User not found (id) : {action.userId}",
        )
        task = self.task_repository.read_by_id(
            action.taskId,
            not_found_message=f"Task not found (id) : {action.taskId}",
        )

        if not task.active:
            raise GoneError(f"Task not active (id) : {task.id}")

        return self.users_actions_repository.add_action_in_task(
            user.id, task.id, action
        )

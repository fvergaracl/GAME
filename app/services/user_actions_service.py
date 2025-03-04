from app.core.exceptions import GoneError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_actions_repository import UserActionsRepository
from app.repository.user_repository import UserRepository
from app.schema.task_schema import (AddActionDidByUserInTask,
                                    ResponseAddActionDidByUserInTask)
from app.schema.user_actions_schema import (CreatedUserActions, CreateUserActions,
                                            CreateUserBodyActions)
from app.services.base_service import BaseService


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
        gameId: str,
        externalTaskId: str,
        action: AddActionDidByUserInTask,
        api_key: str = None,
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
        response = self.game_repository.read_by_column(
            "id",
            gameId,
            not_found_raise_exception=True,
            only_one=True,
            not_found_message=f"Game not found by gameId: {gameId}",
        )
        if user is None:
            user = self.users_repository.create_user_by_externalUserId(
                externalUserId=action.externalUserId
            )
        task = self.task_repository.read_by_column(
            "externalTaskId",
            externalTaskId,
            not_found_message=(f"Task not found (externalTaskId) : {externalTaskId}"),
        )

        if task.status != "open":
            raise GoneError("Task is not active")

        new_action = CreateUserActions(
            typeAction=action.typeAction,
            data=action.data,
            description=action.description,
            userId=str(user.id),
            apiKey_used=api_key,
        )

        created_action = self.user_actions_repository.create(new_action)
        response = ResponseAddActionDidByUserInTask(
            **created_action.dict(),
            externalUserId=str(action.externalUserId),
            message="Action added successfully",
        )
        return response

    def user_add_action_default(
        self,
        externalUserId: str,
        schema: CreateUserBodyActions,
        api_key: str = None,
    ):
        """
        Add action for user.

        Args:
            externalUserId (str): The external user ID.
            schema (CreateUserActions): The action schema.
            api_key (str): The API key.

        Returns:
            object: The added action for user.
        """
        user = self.users_repository.read_by_column(
            "externalUserId",
            externalUserId,
            not_found_raise_exception=False,
        )
        user_created = False
        if user is None:
            user = self.users_repository.create_user_by_externalUserId(
                externalUserId=externalUserId
            )
            user_created = True

        new_action = CreateUserActions(
            **schema.dict(),
            userId=str(user.id),
        )

        created_action = self.user_actions_repository.create(new_action)

        response = CreatedUserActions(
            typeAction=created_action.typeAction,
            description=created_action.description,
            userId=str(user.id),
            is_user_created=user_created,
            message="Action added successfully",
        )
        return response

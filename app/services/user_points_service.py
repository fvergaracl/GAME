from uuid import UUID
from app.services.strategy_service import StrategyService
from app.services.base_service import BaseService
from app.schema.task_schema import TasksWithUsers, BaseUserFirstAction
from app.schema.games_schema import ListTasksWithUsers
from app.schema.user_points_schema import (
    ResponseGetPointsByTask,
    AllPointsByGame,
    TaskPointsByGame,
    PointsAssignedToUser,
    GameDetail,
    TaskDetail
)
from app.core.exceptions import NotFoundError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import (
    WalletTransactionRepository
)


class UserPointsService(BaseService):
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
            user_points_repository: UserPointsRepository,
            users_repository: UserRepository,
            game_repository: GameRepository,
            task_repository: TaskRepository,
            wallet_repository: WalletRepository,
            wallet_transaction_repository: WalletTransactionRepository
    ):
        """
        Initializes the UserPointsService with the provided repositories and
          services.

        Args:
            user_points_repository (UserPointsRepository): The user points
              repository instance.
            users_repository (UserRepository): The user repository instance.
            game_repository (GameRepository): The game repository instance.
            task_repository (TaskRepository): The task repository instance.
            wallet_repository (WalletRepository): The wallet repository
              instance.
            wallet_transaction_repository (WalletTransactionRepository): The
              wallet transaction repository instance.
        """
        self.user_points_repository = user_points_repository
        self.users_repository = users_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        self.wallet_repository = wallet_repository
        self.wallet_transaction_repository = wallet_transaction_repository
        self.strategy_service = StrategyService()
        super().__init__(user_points_repository)

    def query_user_points(self, schema):
        """
        Queries user points based on the provided schema.

        Args:
            schema: The schema for querying user points.

        Returns:
            list: A list of user points matching the schema.
        """
        return self.user_points_repository.read_by_options(schema)

    def get_users_by_gameId(self, gameId):
        """
        Retrieves users associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            ListTasksWithUsers: A list of tasks with associated users.
        """
        game = self.game_repository.read_by_column(
            "id", gameId, not_found_raise_exception=False
        )
        if not game:
            raise NotFoundError(
                detail=f"Game not found by gameId: {game}"
            )
        tasks = self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if not tasks:
            raise NotFoundError(
                detail=f"Tasks not found by gameId: {game.id}"
            )
        response = []
        all_tasks = []
        for task in tasks:
            all_externalUserId = []
            points = self.user_points_repository.get_points_and_users_by_taskId(  # noqa: E501
                task.id
            )

            externalTaskId = task.externalTaskId
            if points:
                for point in points:
                    externalUserId = point.externalUserId
                    user = self.users_repository.read_by_column(
                        "externalUserId",
                        externalUserId,
                        not_found_raise_exception=True
                    )
                    if not user:
                        raise NotFoundError(
                            detail=f"User not found by userId: {point.userId}."
                            f" Please try again later or contact support"
                        )
                    first_user_point = self.user_points_repository.get_first_user_points_in_external_task_id_by_user_id(  # noqa: E501
                        externalTaskId, externalUserId
                    )
                    all_externalUserId.append(
                        BaseUserFirstAction(
                            externalUserId=user.externalUserId,
                            created_at=str(user.created_at),
                            firstAction=str(first_user_point.created_at)
                        ))
            all_tasks = {
                "externalTaskId": externalTaskId,
                "users": all_externalUserId
            }
            response.append(TasksWithUsers(**all_tasks))
        return ListTasksWithUsers(
            gameId=gameId, tasks=response
        )

    def get_points_by_user_list(self, users_list):
        """
        Retrieves points associated with a list of users.

        Args:
            users_list (list): A list of user IDs.

        Returns:
            list: A list of user points details.
        """
        response = []
        for user in users_list:
            user_points = self.get_all_points_by_externalUserId(user)
            response.append(user_points)
        return response

    def get_points_by_externalUserId(self, externalUserId):
        """
        Retrieves points associated with a user by their external user ID.

        Args:
            externalUserId (str): The external user ID.

        Returns:
            list: A list of points details for the user.
        """
        user = self.users_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=True
        )
        if not user:
            raise NotFoundError(
                detail=f"User not found by externalUserId: {externalUserId}"
            )

        tasks_of_users = self.user_points_repository.get_task_by_externalUserId(  # noqa: E501
            externalUserId
        )

        response = []
        for task in tasks_of_users:
            game = self.game_repository.read_by_column(
                "id", task.gameId, not_found_raise_exception=True
            )
            response.append(self.get_points_by_gameId(game.id))

        new_response = []
        for game in response:
            for task in game.task:
                for point in task.points:
                    if point.externalUserId == externalUserId:
                        new_response.append(
                            AllPointsByGame(
                                externalGameId=game.externalGameId,
                                created_at=game.created_at,
                                task=[TaskPointsByGame(
                                    externalTaskId=task.externalTaskId,
                                    points=[PointsAssignedToUser(
                                        externalUserId=point.externalUserId,
                                        points=point.points,
                                        timesAwarded=point.timesAwarded,
                                        pointsData=point.pointsData
                                    )]
                                )]
                            )
                        )
        return new_response

    def get_points_by_gameId(self, gameId: UUID):
        """
        Retrieves points associated with a game by its game ID.

        Args:
            gameId (UUID): The game ID.

        Returns:
            ResponseGetPointsByGame: The points details for the game.
        """
        game = self.game_repository.read_by_column(
            "id", gameId,
            not_found_message=f"Game with gameId: {gameId} not found"
        )
        tasks = self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        response = []
        for task in tasks:
            points = self.user_points_repository.get_points_and_users_by_taskId(  # noqa: E501
                task.id)
            task_detail = TaskDetail(
                externalTaskId=task.externalTaskId,
                points=[ResponseGetPointsByTask(
                    externalUserId=point.externalUserId,
                    points=point.points,
                    timesAwarded=point.timesAwarded,
                    pointsData=point.pointsData
                ) for point in points]
            )
            response.append(task_detail)
        game_detail = GameDetail(
            externalGameId=game.externalGameId,
            created_at=game.created_at,
            task=response
        )
        return game_detail

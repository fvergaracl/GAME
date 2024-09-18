from uuid import UUID

from app.core.config import configs
from app.core.exceptions import (InternalServerError, NotFoundError,
                                 PreconditionFailedError)
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import \
    WalletTransactionRepository
from app.schema.games_schema import ListTasksWithUsers
from app.schema.task_schema import (AssignedPointsToExternalUserId,
                                    BaseUserFirstAction, TasksWithUsers)
from app.schema.user_points_schema import (AllPointsByGame, GameDetail,
                                           PointsAssignedToUser,
                                           ResponseGetPointsByGame,
                                           ResponseGetPointsByTask,
                                           ResponsePointsByExternalUserId,
                                           TaskDetail, TaskPointsByGame,
                                           UserGamePoints, UserPointsAssign)
from app.schema.wallet_schema import CreateWallet
from app.schema.wallet_transaction_schema import BaseWalletTransaction
from app.services.base_service import BaseService
from app.services.strategy_service import StrategyService
from app.util.is_valid_slug import is_valid_slug


class UserPointsService(BaseService):
    def __init__(
        self,
        user_points_repository: UserPointsRepository,
        users_repository: UserRepository,
        game_repository: GameRepository,
        task_repository: TaskRepository,
        wallet_repository: WalletRepository,
        wallet_transaction_repository: WalletTransactionRepository,
    ):
        self.user_points_repository = user_points_repository
        self.users_repository = users_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        self.wallet_repository = wallet_repository
        self.wallet_transaction_repository = wallet_transaction_repository
        self.strategy_service = StrategyService()
        super().__init__(user_points_repository)

    def query_user_points(self, schema):
        return self.user_points_repository.read_by_options(schema)

    def get_users_by_gameId(self, gameId):
        game = self.game_repository.read_by_column(
            "id", gameId, not_found_raise_exception=False
        )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {game}")
        tasks = self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if not tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")
        response = []
        all_tasks = []
        for task in tasks:
            all_externalUserId = []
            points = self.user_points_repository.get_points_and_users_by_taskId(
                task.id)

            externalTaskId = task.externalTaskId
            if points:
                for point in points:

                    externalUserId = point.externalUserId
                    user = self.users_repository.read_by_column(
                        "externalUserId", externalUserId, not_found_raise_exception=True
                    )
                    if not user:
                        raise NotFoundError(
                            detail=f"User not found by userId: {point.userId}. Please try again later or contact support"  # noqa
                        )
                    first_user_point = self.user_points_repository.get_first_user_points_in_external_task_id_by_user_id(
                        externalTaskId, externalUserId
                    )
                    all_externalUserId.append(
                        BaseUserFirstAction(
                            externalUserId=user.externalUserId,
                            created_at=str(user.created_at),
                            firstAction=str(first_user_point.created_at),
                        )
                    )
            all_tasks = {"externalTaskId": externalTaskId,
                         "users": all_externalUserId}
            response.append(TasksWithUsers(**all_tasks))
        return ListTasksWithUsers(gameId=gameId, tasks=response)

    def get_points_by_user_list(self, users_list):
        response = []
        for user in users_list:
            user_points = self.get_all_points_by_externalUserId(user)
            response.append(user_points)
        return response

        # pass}
        return True

    def get_points_by_externalUserId(self, externalUserId):
        user = self.users_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=True
        )
        if not user:
            raise NotFoundError(
                detail=f"User not found by externalUserId: {externalUserId}"
            )

        tasks_of_users = self.user_points_repository.get_task_by_externalUserId(
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
                                task=[
                                    TaskPointsByGame(
                                        externalTaskId=task.externalTaskId,
                                        points=[
                                            PointsAssignedToUser(
                                                externalUserId=point.externalUserId,
                                                points=point.points,
                                                timesAwarded=point.timesAwarded,
                                                pointsData=point.pointsData,
                                            )
                                        ],
                                    )
                                ],
                            )
                        )
        return new_response

    def get_points_by_gameId(self, gameId: UUID):
        game = self.game_repository.read_by_column(
            "id", gameId, not_found_message=f"Game with gameId: {gameId} not found"
        )
        tasks = self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )

        if not tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")
        game_points = []
        for task in tasks:
            user_points = []
            points = self.user_points_repository.get_points_and_users_by_taskId(
                task.id)
            if points:

                for point in points:
                    points_of_user = PointsAssignedToUser(
                        externalUserId=point.externalUserId,
                        points=point.points,
                        timesAwarded=point.timesAwarded,
                        pointsData=point.pointsData,
                    )
                    user_points.append(points_of_user)

            task_points = TaskPointsByGame(
                externalTaskId=task.externalTaskId, points=user_points
            )
            game_points.append(task_points)

        response = AllPointsByGame(
            externalGameId=game.externalGameId,
            created_at=str(game.created_at),
            task=game_points,
        )
        return response

    def get_points_of_user_in_game(self, gameId, externalUserId):
        game = self.game_repository.read_by_column(
            "id", gameId, not_found_raise_exception=False
        )
        if not game:
            raise NotFoundError(detail=f"Game not found by gameId: {gameId}")
        user = self.users_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=False
        )
        if not user:
            raise NotFoundError(
                detail=f"User not found by externalUserId: {externalUserId}"
            )
        tasks = self.task_repository.read_by_column(
            "gameId", game.id, not_found_raise_exception=False, only_one=False
        )
        if not tasks:
            raise NotFoundError(detail=f"Tasks not found by gameId: {game.id}")
        response = []
        for task in tasks:
            points = self.user_points_repository.get_points_and_users_by_taskId(
                task.id)
            if points:
                for point in points:
                    if point.externalUserId == externalUserId:
                        response.append(
                            PointsAssignedToUser(
                                externalUserId=point.externalUserId,
                                points=point.points,
                                timesAwarded=point.timesAwarded,
                            )
                        )
        return response

    def assign_points_to_user(self, gameId, externalTaskId, schema):
        externalUserId = schema.externalUserId
        is_a_created_user = False

        game = self.game_repository.read_by_column(
            column="id",
            value=gameId,
            not_found_message=(f"Game with gameId {gameId} not found"),
            only_one=True,
        )
        externalGameId = game.externalGameId
        task = self.task_repository.read_by_gameId_and_externalTaskId(
            game.id, externalTaskId
        )
        if not task:
            raise NotFoundError(
                f"Task not found with externalTaskId: {externalTaskId}")

        strategyId = task.strategyId
        strategy = self.strategy_service.get_strategy_by_id(strategyId)

        if not strategy:
            raise NotFoundError(
                f"Strategy not found with id: {strategyId} for task with externalTaskId: {externalTaskId}"  # noqa
            )

        user = self.users_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=False
        )
        if not user:
            is_valid_externalUserId = is_valid_slug(externalUserId)
            if not is_valid_externalUserId:
                raise PreconditionFailedError(
                    detail=(
                        f"Invalid externalUserId: {externalUserId}. externalUserId should be a valid (Should have only alphanumeric characters and Underscore . Length should be between 3 and 50)"  # noqa
                    )
                )
            user = self.users_repository.create_user_by_externalUserId(
                externalUserId=externalUserId
            )
            is_a_created_user = True

        strategy_instance = self.strategy_service.get_Class_by_id(strategyId)

        try:
            points, case_name = strategy_instance.calculate_points(
                externalGameId=externalGameId,
                externalTaskId=externalTaskId,
                externalUserId=externalUserId,
                data=schema.data,
            )
        except Exception as e:
            print("----------------- ERROR -----------------")
            print(e)
            print("----------------- ERROR -----------------")
            raise InternalServerError(
                detail=(
                    f"Error in calculate points for task with externalTaskId: {externalTaskId} and user with externalUserId: {externalUserId}. Please try again later or contact support"  # noqa
                )
            )
        if points == -1:
            raise PreconditionFailedError(
                detail=(
                    case_name
                )
            )
        if points == 0:
            raise PreconditionFailedError(
                detail=(
                    f"Points not calculated for task with externalTaskId: {externalTaskId} and user with externalUserId: {externalUserId}. Please try again later or contact support"  # noqa
                )
            )
        if not points or not case_name:
            raise InternalServerError(
                detail=(
                    f"Points not calculated for task with externalTaskId: {externalTaskId} and user with externalUserId: {externalUserId}. Beacuse the strategy don't have condition to calculate it or the strategy don't have a case name"  # noqa
                )
            )
        print(f"points: {points} | case_name: {case_name}")

        user_points_schema = UserPointsAssign(
            userId=str(user.id),
            taskId=str(task.id),
            points=points,
            caseName=case_name,
            data=schema.data,
            description="Points assigned by GAME",
        )
        user_points = self.user_points_repository.create(user_points_schema)
        wallet = self.wallet_repository.read_by_column(
            "userId", user.id, not_found_raise_exception=False
        )
        if wallet:
            wallet.pointsBalance += points
            self.wallet_repository.update(wallet.id, wallet)

        if not wallet:
            new_wallet = CreateWallet(
                userId=str(user.id),
                points=points,
                coinsBalance=0,
                pointsBalance=points,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
            )
            wallet = self.wallet_repository.create(new_wallet)
        wallet_transaction = BaseWalletTransaction(
            transactionType="AssignPoints",
            points=points,
            coins=0,
            data=schema.data,
            appliedConversionRate=0,
            walletId=str(wallet.id),
        )
        wallet_transaction_repository = self.wallet_transaction_repository.create(
            wallet_transaction
        )
        if not wallet_transaction_repository:
            raise InternalServerError(
                detail=(
                    f"Wallet transaction not created for user with externalUserId: {externalUserId} and task with externalTaskId: {externalTaskId}. Please try again later or contact support"  # noqa
                )
            )

        response = AssignedPointsToExternalUserId(
            points=points,
            externalUserId=externalUserId,
            isACreatedUser=is_a_created_user,
            gameId=gameId,
            externalTaskId=externalTaskId,
            caseName=case_name,
            created_at=str(user_points.created_at),
        )
        return response

    def get_users_points_by_externalGameId(self, externalGameId):
        game = self.game_repository.read_by_column(
            column="externalGameId",
            value=externalGameId,
            not_found_message=(
                f"Game with externalGameId {externalGameId} not found"),
        )

        tasks = self.task_repository.read_by_column(
            "gameId", game.id, only_one=False, not_found_raise_exception=False
        )

        if tasks:
            tasks = [task.id for task in tasks]

        if not tasks:
            raise NotFoundError(
                f"The game with externalGameId {externalGameId} has no tasks"
            )

        response = []
        for task in tasks:
            points = self.user_points_repository.get_points_and_users_by_taskId(
                task)
            response_by_task = []
            if points:
                for point in points:
                    response_by_task.append(
                        ResponseGetPointsByTask(
                            externalUserId=point.externalUserId, points=point.points
                        )
                    )

            if response_by_task:
                response.append(
                    ResponseGetPointsByGame(
                        externalTaskId=point.externalTaskId, points=response_by_task
                    )
                )

        return response

    def get_users_points_by_externalTaskId(self, externalTaskId):
        task = self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=(
                f"Task with externalTaskId {externalTaskId} not found"),
        )

        points_by_task = self.user_points_repository.get_points_and_users_by_taskId(
            task.id
        )
        cleaned_points_by_task = []
        if points_by_task:
            for point in points_by_task:
                cleaned_points_by_task.append(
                    ResponseGetPointsByTask(
                        externalUserId=point.externalUserId, points=point.points
                    )
                )
        return cleaned_points_by_task

    def get_users_points_by_externalTaskId_and_externalUserId(
        self, externalTaskId, externalUserId
    ):
        task = self.task_repository.read_by_column(
            column="externalTaskId",
            value=externalTaskId,
            not_found_message=(
                f"Task with externalTaskId {externalTaskId} not found"),
        )
        user = self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=(
                f"User with externalUserId {externalUserId} not found"),
        )

        points = self.user_points_repository.read_by_columns(
            {"taskId": task.id, "userId": user.id}
        )

        return points

    def get_all_points_by_externalUserId(self, externalUserId):
        user_data = self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=(
                f"User with externalUserId {externalUserId} not found"),
            not_found_raise_exception=False,
        )
        if not user_data:
            return UserGamePoints(
                externalUserId=externalUserId,
                points=0,
                timesAwarded=0,
                games=[],
                userExists=False,
            )

        tasks = self.user_points_repository.get_task_by_externalUserId(
            externalUserId)

        response = []
        for task in tasks:
            game = self.game_repository.read_by_column(
                "id", task.gameId, not_found_raise_exception=True
            )
            response.append(self.get_points_by_gameId(game.id))

        for game in response:
            # UserGamePoints
            points = 0
            times_awarded = 0
            games = []
            for task in game.task:
                # GameDetail
                task_points = 0
                task_times_awarded = 0
                tasks = []
                for point in task.points:
                    if point.externalUserId == externalUserId:
                        task_points += point.points
                        task_times_awarded += point.timesAwarded
                        if point.points > 0:
                            tasks.append(
                                TaskDetail(
                                    externalTaskId=task.externalTaskId,
                                    pointsData=point.pointsData,
                                )
                            )
                points += task_points
                times_awarded += task_times_awarded
                if points > 0 and len(tasks) > 0:
                    games.append(
                        GameDetail(
                            externalGameId=game.externalGameId,
                            points=task_points,
                            timesAwarded=task_times_awarded,
                            tasks=tasks,
                        )
                    )
            return UserGamePoints(
                externalUserId=externalUserId,
                points=points,
                timesAwarded=times_awarded,
                games=games,
            )

        return None

    def get_points_of_user(self, externalUserId):
        user = self.users_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=(
                f"User with externalUserId {externalUserId} not found"),
        )

        points = self.user_points_repository.get_task_and_sum_points_by_userId(
            user.id)

        total_points = 0
        for point in points:
            total_points += point.points

        response = ResponsePointsByExternalUserId(
            externalUserId=externalUserId,
            points=total_points,
            points_by_task=points,  # noqa
        )
        return response

    def count_measurements_by_external_task_id(self, external_task_id):
        return self.user_points_repository.count_measurements_by_external_task_id(
            external_task_id
        )  # noqa

    def get_user_task_measurements_count(self, externalTaskId, externalUserId):
        return self.user_points_repository.get_user_task_measurements_count(
            externalTaskId, externalUserId
        )

    def get_user_task_measurements_count_the_last_seconds(
        self, externalTaskId, externalUserId, seconds
    ):
        return self.user_points_repository.get_user_task_measurements_count_the_last_seconds(
            externalTaskId, externalUserId, seconds
        )

    def get_avg_time_between_tasks_by_user_and_game_task(
        self, externalGameId, externalTaskId, externalUserId
    ):
        return self.user_points_repository.get_avg_time_between_tasks_by_user_and_game_task(  # noqa
            externalGameId, externalTaskId, externalUserId
        )

    def get_avg_time_between_tasks_for_all_users(self, externalGameId, externalTaskId):
        return self.user_points_repository.get_avg_time_between_tasks_for_all_users(  # noqa
            externalGameId, externalTaskId
        )

    def get_last_window_time_diff(self, externalTaskId, externalUserId):
        return self.user_points_repository.get_last_window_time_diff(
            externalTaskId, externalUserId
        )

    def get_new_last_window_time_diff(
        self, externalTaskId, externalUserId, externalGameId
    ):
        return self.user_points_repository.get_new_last_window_time_diff(
            externalTaskId, externalUserId, externalGameId
        )

    def get_user_task_measurements(self, externalTaskId, externalUserId):
        return self.user_points_repository.get_user_task_measurements(
            externalTaskId, externalUserId
        )

    # get count personal points in the game, should have "minutes" field in the data
    def count_personal_records_by_external_game_id(
            self, external_game_id, externalUserId
    ):
        """
        Count the number of records for a user in a game.

        Args:
            external_game_id (str): The external game id.
            externalUserId (str): The external user id.

        Returns:
            int: The number of records.
        """
        return self.user_points_repository.count_personal_records_by_external_game_id(
            external_game_id,
            externalUserId
        )

    def user_has_record_before_in_externalTaskId_last_min(
        self, externalTaskId, externalUserId, minutes
    ):
        """
        Check if a user has a record before in the task in the last minute.

        Args:
            externalTaskId (str): The external task id.
            externalUserId (str): The external user id.
            minutes (int): The number of minutes.

        Returns:
            bool: True if the user has a record before in the task,
              False otherwise
        """
        return self.user_points_repository.user_has_record_before_in_externalTaskId_last_min(
            externalTaskId, externalUserId, minutes
        )

    def get_global_avg_by_external_game_id(self, external_game_id):
        """
        Get the global average time rewarded. It does not take into account
          the time with 0 value (minutes)

        Args:
            external_game_id (str): The external game id.

        Returns:
            float: The global average.
        """
        return self.user_points_repository.get_global_avg_by_external_game_id(
            external_game_id
        )

    def get_personal_avg_by_external_game_id(self, external_game_id, externalUserId):
        """
        Get the personal average time rewarded. It does not take into account
          the time with 0 value (minutes)

        Args:
            external_game_id (str): The external game id.
            externalUserId (str): The external user id.

        Returns:
            float: The personal average.
        """
        return self.user_points_repository.get_personal_avg_by_external_game_id(
            external_game_id, externalUserId
        )

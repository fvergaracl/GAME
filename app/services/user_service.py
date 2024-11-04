import copy

from app.core.config import configs
from app.repository.task_repository import TaskRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import WalletTransactionRepository
from app.schema.task_schema import TaskPointsResponseByUser
from app.schema.user_points_schema import BaseUserPointsBaseModel, UserPointsAssigned
from app.schema.user_schema import (
    PostPointsConversionRequest,
    ResponsePointsConversion,
    UserPointsTasks,
    UserWallet,
)
from app.schema.wallet_schema import CreateWallet
from app.schema.wallet_transaction_schema import BaseWalletTransaction
from app.services.base_service import BaseService
from app.util.serialize_wallet import serialize_wallet


class UserService(BaseService):
    """
    Service class for managing users.

    Attributes:
        user_repository (UserRepository): Repository instance for users.
        user_points_repository (UserPointsRepository): Repository instance for
          user points.
        task_repository (TaskRepository): Repository instance for tasks.
        wallet_repository (WalletRepository): Repository instance for wallets.
        wallet_transaction_repository (WalletTransactionRepository):
          Repository instance for wallet transactions.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        user_points_repository: UserPointsRepository,
        task_repository: TaskRepository,
        wallet_repository: WalletRepository,
        wallet_transaction_repository: WalletTransactionRepository,
    ):
        """
        Initializes the UserService with the provided repositories.

        Args:
            user_repository (UserRepository): The user repository instance.
            user_points_repository (UserPointsRepository): The user points
              repository instance.
            task_repository (TaskRepository): The task repository instance.
            wallet_repository (WalletRepository): The wallet repository
              instance.
            wallet_transaction_repository (WalletTransactionRepository): The
              wallet transaction repository instance.
        """
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        self.task_repository = task_repository
        self.wallet_repository = wallet_repository
        self.wallet_transaction_repository = wallet_transaction_repository
        super().__init__(user_repository)

    def basic_engagement_points(self):
        """
        Provides a fixed number of points as a basic engagement reward for a
          user's initial actions within the gamification system.

        Returns:
            int: The fixed number of basic engagement points.
        """
        basic_points = 1

        return basic_points

    def performance_penalty_points(self):
        """
        Calculates the number of points to deduct as a penalty for performance
          below a certain threshold.

        Returns:
            int: The number of points to deduct.
        """
        penalty_points = -5

        return penalty_points

    def performance_bonus_points(self):
        """
        Calculates the number of additional points to award for performance
          above a certain threshold.

        Returns:
            int: The number of bonus points to award.
        """
        bonus_points = 10

        return bonus_points

    def individual_over_global_points(self):
        """
        Awards additional points for users who have improved their individual
          performance compared to their own history, even if below the global
            average.

        Returns:
            int: The number of additional points to award.
        """
        improvement_points = 5

        return improvement_points

    def need_for_motivation_points(self):
        """
        Provides a small point incentive for users who are underperforming
          both individually and globally, to motivate improvement.

        Returns:
            int: The number of points to award as motivation.
        """
        motivation_points = 2

        return motivation_points

    def peak_performer_bonus_points(self):
        """
        Rewards users who have exceeded both their individual performance and
          the global average, standing out as peak performers in the system.

        Returns:
            int: The number of bonus points for peak performers.
        """
        peak_points = 15

        return peak_points

    def global_advantage_adjustment_points(self):
        """
        Awards additional points to users whose performance is above the
          global average but have shown a decrease in their individual
            performance. It's designed to encourage users to strive for
              above-average performance, recognizing their effort amidst
                challenges.

        Returns:
            int: The number of adjustment points for maintaining a global
              advantage.
        """
        adjustment_points = 7

        return adjustment_points

    def individual_adjustment_points(self):
        """
        Rewards users who have improved their individual performance,
          regardless of their standing against the global average. It aims to
            acknowledge and encourage personal improvement, motivating users
              to keep advancing.

        Returns:
            int: The number of points to award for individual performance
              improvement.
        """
        improvement_points = 8

        return improvement_points

    def create_user(self, schema):
        """
        Creates a new user using the provided schema.

        Args:
            schema: The schema representing the user to be created.

        Returns:
            object: The created user.
        """
        return self.user_repository.create(schema)

    def assign_points_to_user(self, userId, schema: BaseUserPointsBaseModel):
        """
        Assigns points to a user based on the provided schema.

        Args:
            userId (str): The user ID.
            schema (BaseUserPointsBaseModel): The schema containing point
              assignment details.

        Returns:
            UserPointsAssigned: The assigned points details.
        """
        user = self.user_repository.read_by_id(
            userId, not_found_message=f"User not found with userId: {userId}"
        )
        points = schema.points
        measurement_count = self.user_points_repository.get_user_measurement_count(
            userId
        )  # noqa: E501
        start_time_last_task = (
            self.user_points_repository.get_start_time_for_last_task(  # noqa: E501
                userId
            )
        )
        end_time_last_task = (
            self.user_points_repository.get_time_taken_for_last_task(  # noqa: E501
                userId
            )
        )

        if end_time_last_task and start_time_last_task:
            duration_last_task = (
                end_time_last_task - start_time_last_task
            ).total_seconds() / 60
        else:
            duration_last_task = 0

        individual_calculation = self.user_points_repository.get_individual_calculation(
            userId
        )  # noqa: E501

        global_calculation = (
            self.user_points_repository.get_global_calculation()
        )  # noqa: E501
        schema.data["label_function_choose"] = "-"
        if not points:
            if measurement_count <= 2:
                points = self.basic_engagement_points()
                schema.data["label_function_choose"] = (
                    "basic_engagement_points"  # noqa: E501
                )
            elif measurement_count == 2:
                if duration_last_task > global_calculation:
                    points = self.performance_penalty_points()
                    schema.data["label_function_choose"] = (
                        "performance_penalty_points"  # noqa: E501
                    )
                else:
                    points = self.performance_bonus_points()
                    schema.data["label_function_choose"] = (
                        "performance_bonus_points"  # noqa: E501
                    )
            else:
                if duration_last_task >= individual_calculation:
                    if (
                        duration_last_task < individual_calculation
                        and duration_last_task > global_calculation
                    ):
                        points = self.individual_over_global_points()
                        schema.data["label_function_choose"] = (
                            "individual_over_global_points"
                        )
                    elif (
                        duration_last_task > individual_calculation
                        and duration_last_task > global_calculation
                    ):
                        points = self.need_for_motivation_points()
                        schema.data["label_function_choose"] = (
                            "need_for_motivation_points"
                        )
                    elif (
                        duration_last_task < individual_calculation
                        and duration_last_task < global_calculation
                    ):
                        points = self.peak_performer_bonus_points()
                        schema.data["label_function_choose"] = (
                            "peak_performer_bonus_points"
                        )
                    else:
                        points = self.global_advantage_adjustment_points()
                        schema.data["label_function_choose"] = (
                            "global_advantage_adjustment_points"
                        )
                else:
                    points = self.individual_adjustment_points()
                    schema.data["label_function_choose"] = (
                        "individual_adjustment_points"
                    )

        user_points_schema = BaseUserPointsBaseModel(
            userId=str(user.id),
            taskId=str(schema.taskId),
            points=points,
            data=schema.data,
            description=schema.description,
        )

        user_points = self.user_points_repository.create(user_points_schema)

        wallet = self.wallet_repository.read_by_column(
            "userId", str(user.id), not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=points,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id),
            )

            wallet = self.wallet_repository.create(new_wallet)
        else:
            wallet.pointsBalance += points
            self.wallet_repository.update(wallet.id, wallet)

        wallet_transaction = BaseWalletTransaction(
            transactionType="AssignPoints",
            points=points,
            coins=0,
            appliedConversionRate=wallet.conversionRate,
            walletId=str(wallet.id),
        )
        self.wallet_transaction_repository.create(wallet_transaction)

        response = UserPointsAssigned(
            id=str(user_points.id),
            created_at=user_points.created_at,
            updated_at=user_points.updated_at,
            description=user_points.description,
            userId=str(user_points.userId),
            taskId=str(user_points.taskId),
            points=user_points.points,
            data=user_points.data,
            wallet=wallet,
        )

        return response

    def get_wallet_by_user_id(self, userId):
        """
        Retrieves the wallet associated with a user by their user ID.

        Args:
            userId (str): The user ID.

        Returns:
            UserWallet: The wallet details.
        """
        user = self.user_repository.read_by_id(
            userId, not_found_message=f"User not found with userId: {userId}"
        )
        wallet = self.wallet_repository.read_by_column(
            "userId", str(user.id), not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=0,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id),
            )

            wallet = self.wallet_repository.create(new_wallet)

        wallet_transactions = (
            self.wallet_transaction_repository.read_by_column(  # noqa: E501
                "walletId",
                str(wallet.id),
                only_one=False,
                not_found_raise_exception=False,
            )
        )
        for transaction in wallet_transactions:
            transaction.created_at = str(transaction.created_at)
        response = UserWallet(
            userId=str(user.id), wallet=wallet, walletTransactions=wallet_transactions
        )

        return response

    def get_wallet_by_externalUserId(self, externalUserId):
        """
        Retrieves the wallet associated with a user by their external user ID.

        Args:
            externalUserId (str): The external user ID.

        Returns:
            UserWallet: The wallet details.
        """
        user = self.user_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=True
        )
        response = self.get_wallet_by_user_id(str(user.id))
        return response

    def get_points_by_user_id(self, userId):
        """
        Retrieves points associated with a user by their user ID.

        Args:
            userId (str): The user ID.

        Returns:
            UserPointsTasks: The user's points and associated tasks.
        """
        user = self.user_repository.read_by_id(
            userId, not_found_message=f"User not found with userId: {userId}"
        )
        tasks = self.user_points_repository.read_by_column(
            "userId", str(user.id), only_one=False, not_found_raise_exception=False
        )
        tasks = list({v.taskId: v for v in tasks}.values())
        if not tasks:
            response = UserPointsTasks(id=str(user.id), tasks=[])
            return response

        cleaned_tasks = []
        for task in tasks:
            taskId = str(task.taskId)
            task.userId = str(task.userId)
            task = self.task_repository.read_by_id(
                taskId, not_found_message="Task not found by id: {taskId}"
            )
            all_points = self.user_points_repository.get_points_and_users_by_taskId(  # noqa: E501
                taskId
            )
            points = 0
            if all_points:
                for point in all_points:
                    if point.userId == userId:
                        points = point.points

            cleaned_tasks.append(
                TaskPointsResponseByUser(
                    taskId=str(task.id),
                    externalTaskId=task.externalTaskId,
                    gameId=str(task.gameId),
                    points=points,
                )
            )
        response = UserPointsTasks(id=str(user.id), tasks=cleaned_tasks)
        return response

    def preview_points_to_coins_conversion(self, userId, points):
        """
        Previews the conversion of points to coins for a user.

        Args:
            userId (str): The user ID.
            points (int): The number of points to convert.

        Returns:
            dict: The conversion preview details.
        """
        if not points:
            raise ValueError("Points must be provided")

        if points <= 0:
            raise ValueError("Points must be greater than 0")

        user = self.user_repository.read_by_id(
            userId, not_found_message=f"User not found with userId: {userId}"
        )
        wallet = self.wallet_repository.read_by_column(
            "userId", str(user.id), not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=0,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id),
            )

            wallet = self.wallet_repository.create(new_wallet)

        coins = points / wallet.conversionRate
        haveEnoughPoints = True
        if wallet.pointsBalance < points:
            haveEnoughPoints = False

        response = {
            "points": points,
            "conversionRate": wallet.conversionRate,
            "conversionRateDate": str(wallet.updated_at),
            "convertedAmount": coins,
            "convertedCurrency": "coins",
            "haveEnoughPoints": haveEnoughPoints,
        }
        return response

    def preview_points_to_coins_conversion_externalUserId(self, externalUserId, points):
        """
        Previews the conversion of points to coins for a user by their
          external user ID.

        Args:
            externalUserId (str): The external user ID.
            points (int): The number of points to convert.

        Returns:
            dict: The conversion preview details.
        """
        user = self.user_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=True
        )
        response = self.preview_points_to_coins_conversion(str(user.id), points)
        return response

    def convert_points_to_coins(
        self, userId, schema: PostPointsConversionRequest, api_key
    ):
        """
        Converts points to coins for a user based on the provided schema.

        Args:
            userId (str): The user ID.
            schema (PostPointsConversionRequest): The schema containing
              conversion details.
              api_key (str): The API key.

        Returns:
            ResponsePointsConversion: The conversion details.
        """
        points = schema.points
        if not points:
            raise ValueError("Points must be provided")

        if points <= 0:
            raise ValueError("Points must be greater than 0")

        user = self.user_repository.read_by_id(
            userId, not_found_message=f"User not found with userId: {userId}"
        )
        wallet = self.wallet_repository.read_by_column(
            "userId", str(user.id), not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=0,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id),
                apiKey_used=api_key,
            )

            wallet = self.wallet_repository.create(new_wallet)

        wallet_before = copy.deepcopy(wallet)

        coins = points / wallet.conversionRate
        haveEnoughPoints = True

        if wallet.pointsBalance < points:
            haveEnoughPoints = False

        if not haveEnoughPoints:
            raise ValueError("Not enough points")

        wallet.pointsBalance -= points
        wallet.coinsBalance += coins
        self.wallet_repository.update(wallet.id, wallet)

        wallet_before_serializable = serialize_wallet(wallet_before)
        wallet_serializable = serialize_wallet(wallet)

        wallet_transaction = BaseWalletTransaction(
            transactionType="ConvertPointsToCoins",
            points=points,
            coins=coins,
            appliedConversionRate=wallet.conversionRate,
            walletId=str(wallet.id),
            data={
                "walletBefore": wallet_before_serializable,
                "walletAfter": wallet_serializable,
            },
            apiKey_used=api_key,
        )

        transaction = self.wallet_transaction_repository.create(wallet_transaction)

        response = {
            "transactionId": str(transaction.id),
            "points": points,
            "conversionRate": wallet.conversionRate,
            "conversionRateDate": str(wallet.updated_at),
            "convertedAmount": coins,
            "convertedCurrency": "coins",
            "haveEnoughPoints": haveEnoughPoints,
        }
        response = ResponsePointsConversion(**response)
        return response

    def convert_points_to_coins_externalUserId(
        self, externalUserId, schema: PostPointsConversionRequest, api_key: str = None
    ):
        """
        Converts points to coins for a user by their external user ID based on
          the provided schema.

        Args:
            externalUserId (str): The external user ID.
            schema (PostPointsConversionRequest): The schema containing
              conversion details.
            api_key (str): The API key.

        Returns:
            ResponsePointsConversion: The conversion details.
        """
        user = self.user_repository.read_by_column(
            "externalUserId", externalUserId, not_found_raise_exception=True
        )
        response = self.convert_points_to_coins(str(user.id), schema, api_key)
        return response

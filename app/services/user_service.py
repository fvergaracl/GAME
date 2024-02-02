from app.repository.user_repository import UserRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.task_repository import TaskRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import (
    WalletTransactionRepository
)
from app.services.base_service import BaseService
from app.schema.user_schema import (
    CreateWallet,
    UserWallet,
    UserPointsTasks,
    PostPointsConversionRequest,
    ResponsePointsConversion
)
from app.schema.task_schema import TaskPointsResponseByUser
from app.schema.user_points_schema import (
    BaseUserPointsBaseModel, UserPointsAssigned
)
from app.schema.wallet_transaction_schema import BaseWalletTransaction
from app.core.config import configs
from app.util.serialize_wallet import serialize_wallet
import copy


class UserService(BaseService):
    def __init__(
            self,
            user_repository: UserRepository,
            user_points_repository: UserPointsRepository,
            task_repository: TaskRepository,
            wallet_repository: WalletRepository,
            wallet_transaction_repository: WalletTransactionRepository
    ):
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
        self.task_repository = task_repository
        self.wallet_repository = wallet_repository
        self.wallet_transaction_repository = wallet_transaction_repository
        super().__init__(user_repository)

    def create_user(self, schema):
        return self.user_repository.create(schema)

    def assign_points_to_user(
            self,
            userId,
            schema: BaseUserPointsBaseModel
    ):
        user = self.user_repository.read_by_id(
            userId,
            not_found_message=f"User not found with userId: {userId}"
        )
        points = schema.points
        if not points:
            # ACA se debe llamar a la funcion que calcula los puntos WIP
            raise ValueError("Points must be provided")

        user_points_schema = BaseUserPointsBaseModel(
            userId=str(user.id),
            taskId=str(schema.taskId),
            points=points,
            data=schema.data
        )

        user_points = self.user_points_repository.create(user_points_schema)

        wallet = self.wallet_repository.read_by_column(
            "userId",
            str(user.id),
            not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=points,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id)
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
            walletId=str(wallet.id)
        )
        self.wallet_transaction_repository.create(wallet_transaction)

        response = UserPointsAssigned(
            id=str(user_points.id),
            created_at=user_points.created_at,
            updated_at=user_points.updated_at,
            userId=str(user_points.userId),
            taskId=str(user_points.taskId),
            points=user_points.points,
            data=user_points.data,
            wallet=wallet

        )

        return response

    def get_wallet_by_user_id(self, userId):
        user = self.user_repository.read_by_id(
            userId,
            not_found_message=f"User not found with userId: {userId}"
        )
        wallet = self.wallet_repository.read_by_column(
            "userId",
            str(user.id),
            not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=0,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id)
            )

            wallet = self.wallet_repository.create(new_wallet)

        wallet_transactions = self.wallet_transaction_repository.read_by_column(
            "walletId",
            str(wallet.id),
            only_one=False,
            not_found_raise_exception=False
        )

        response = UserWallet(
            userId=str(user.id),
            wallet=wallet,
            walletTransactions=wallet_transactions
        )

        return response

    def get_points_by_user_id(self, userId):
        user = self.user_repository.read_by_id(
            userId,
            not_found_message=f"User not found with userId: {userId}"
        )
        tasks = self.user_points_repository.read_by_column(
            "userId",
            str(user.id),
            only_one=False,
            not_found_raise_exception=False
        )
        tasks = list({v.taskId: v for v in tasks}.values())
        if (not tasks):
            response = UserPointsTasks(
                id=str(user.id),
                tasks=[]
            )
            return response

        cleaned_tasks = []
        for task in tasks:
            taskId = str(task.taskId)
            task.userId = str(task.userId)
            task = self.task_repository.read_by_id(
                taskId,
                not_found_message="Task not found by id : {taskId}"
            )
            all_points = self.user_points_repository.get_points_and_users_by_taskId(
                taskId)
            points = 0
            if (all_points):
                for point in all_points:
                    if (point.userId == userId):
                        points = point.points

            cleaned_tasks.append(TaskPointsResponseByUser(
                taskId=str(task.id),
                externalTaskId=task.externalTaskId,
                gameId=str(task.gameId),
                points=points
            ))
        response = UserPointsTasks(
            id=str(user.id),
            tasks=cleaned_tasks
        )
        return response

    def preview_points_to_coins_conversion(self, userId, points):

        if not points:
            raise ValueError("Points must be provided")

        if (points <= 0):
            raise ValueError("Points must be greater than 0")

        user = self.user_repository.read_by_id(
            userId,
            not_found_message=f"User not found with userId: {userId}"
        )
        wallet = self.wallet_repository.read_by_column(
            "userId",
            str(user.id),
            not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=0,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id)
            )

            wallet = self.wallet_repository.create(new_wallet)

        # check if have enough points
        coins = points / wallet.conversionRate
        haveEnoughPoints = True
        if (wallet.pointsBalance < points):
            haveEnoughPoints = False

        response = {
            "points": points,
            "conversionRate": wallet.conversionRate,
            "conversionRateDate": str(wallet.updated_at),
            "convertedAmount": coins,
            "convertedCurrency": "coins",
            "haveEnoughPoints": haveEnoughPoints
        }
        return response

    def convert_points_to_coins(self, userId, schema: PostPointsConversionRequest):
        points = schema.points
        if not points:
            raise ValueError("Points must be provided")

        if (points <= 0):
            raise ValueError("Points must be greater than 0")

        user = self.user_repository.read_by_id(
            userId,
            not_found_message=f"User not found with userId: {userId}"
        )
        wallet = self.wallet_repository.read_by_column(
            "userId",
            str(user.id),
            not_found_raise_exception=False
        )
        if not wallet:
            new_wallet = CreateWallet(
                coinsBalance=0,
                pointsBalance=0,
                conversionRate=configs.DEFAULT_CONVERTION_RATE_POINTS_TO_COIN,
                userId=str(user.id)
            )

            wallet = self.wallet_repository.create(new_wallet)

        wallet_before = copy.deepcopy(wallet)

        # check if have enough points
        coins = points / wallet.conversionRate
        haveEnoughPoints = True

        if (wallet.pointsBalance < points):
            haveEnoughPoints = False

        if (not haveEnoughPoints):
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
                "walletAfter": wallet_serializable
            }

        )

        transaction = self.wallet_transaction_repository.create(
            wallet_transaction)

        response = {
            "transactionId": str(transaction.id),
            "points": points,
            "conversionRate": wallet.conversionRate,
            "conversionRateDate": str(wallet.updated_at),
            "convertedAmount": coins,
            "convertedCurrency": "coins",
            "haveEnoughPoints": haveEnoughPoints
        }
        response = ResponsePointsConversion(**response)
        return response

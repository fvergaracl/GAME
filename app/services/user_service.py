from app.repository.user_repository import UserRepository
from app.repository.user_points_repository import UserPointsRepository
from app.repository.wallet_repository import WalletRepository
from app.repository.wallet_transaction_repository import WalletTransactionRepository
from app.services.base_service import BaseService
from app.schema.user_schema import CreateWallet
from app.schema.user_points_schema import BaseUserPointsBaseModel, UserPointsAssigned
from app.schema.wallet_transaction_schema import BaseWalletTransaction
from app.core.config import configs


class UserService(BaseService):
    def __init__(
            self,
            user_repository: UserRepository,
            user_points_repository: UserPointsRepository,
            wallet_repository: WalletRepository,
            wallet_transaction_repository: WalletTransactionRepository
    ):
        self.user_repository = user_repository
        self.user_points_repository = user_points_repository
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

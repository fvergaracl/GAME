from app.repository.user_repository import UserRepository
from app.repository.wallet_repository import WalletRepository
from app.schema.wallet_schema import BaseWallet, ResponsePreviewConvertPoints
from app.services.base_service import BaseService


class WalletService(BaseService):
    """
    Service class for managing wallets.
    """

    def __init__(
        self, wallet_repository: WalletRepository, user_repository: UserRepository
    ):
        self.wallet_repository = wallet_repository
        self.user_repository = user_repository
        super().__init__(wallet_repository)

    async def get_wallet_by_user_id(self, externalUserId):
        user = await self.user_repository.read_by_column(
            column="externalUserId",
            value=externalUserId,
            not_found_message=f"User with externalUserId "
            f"{externalUserId} not found",
        )

        wallet = await self.wallet_repository.read_by_column(
            column="userId",
            value=user.id,
            not_found_message=f"Wallet with userId {user.id} not found",
        )

        return BaseWallet(
            id=wallet.id,
            coinsBalance=wallet.coinsBalance,
            pointsBalance=wallet.pointsBalance,
            conversionRate=wallet.conversionRate,
            externalUserId=user.externalUserId,
            created_at=wallet.created_at,
            updated_at=wallet.updated_at,
        )

    async def preview_convert(self, schema):
        user = await self.user_repository.read_by_column(
            column="externalUserId",
            value=schema.externalUserId,
            not_found_message=f"User with externalUserId "
            f"{schema.externalUserId} not found",
        )

        wallet = await self.wallet_repository.read_by_column(
            column="userId",
            value=user.id,
            not_found_message=f"Wallet with userId {user.id} not found",
        )

        points_converted = schema.points * wallet.conversionRate

        return ResponsePreviewConvertPoints(
            coins=points_converted,
            points_converted=schema.points,
            conversionRate=wallet.conversionRate,
            afterConversionPoints=wallet.pointsBalance - schema.points,
            afterConversionCoins=wallet.coinsBalance + points_converted,
            externalUserId=schema.externalUserId,
        )

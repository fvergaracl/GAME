from app.repository.wallet_repository import WalletRepository
from app.services.base_service import BaseService


class WalletService(BaseService):
    def __init__(self, wallet_repository: WalletRepository):
        self.wallet_repository = wallet_repository
        super().__init__(wallet_repository)

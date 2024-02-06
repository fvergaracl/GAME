from app.repository.wallet_transaction_repository import (
    WalletTransactionRepository
)
from app.services.base_service import BaseService


class WalletTransactionService(BaseService):
    def __init__(
            self,
            wallet_transaction_repository: WalletTransactionRepository
    ):
        self.wallet_transaction_repository = wallet_transaction_repository
        super().__init__(wallet_transaction_repository)

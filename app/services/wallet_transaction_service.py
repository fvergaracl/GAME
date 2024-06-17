from app.repository.wallet_transaction_repository import (
    WalletTransactionRepository
)
from app.services.base_service import BaseService


class WalletTransactionService(BaseService):
    """
    Service class for wallet transactions.

    Attributes:
        wallet_transaction_repository (WalletTransactionRepository):
          Repository instance for wallet transactions.
    """

    def __init__(
            self, wallet_transaction_repository: WalletTransactionRepository):
        """
        Initializes the WalletTransactionService with the provided repository.

        Args:
            wallet_transaction_repository (WalletTransactionRepository): The
              repository instance.
        """
        self.wallet_transaction_repository = wallet_transaction_repository
        super().__init__(wallet_transaction_repository)

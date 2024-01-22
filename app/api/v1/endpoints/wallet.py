from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container

from app.services.wallet_service import WalletService

router = APIRouter(
    prefix="/wallet",
    tags=["wallet"],
)

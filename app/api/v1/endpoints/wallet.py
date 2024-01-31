from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.wallet_schema import (
    BaseWallet,
    PostPreviewConvertPoints,
    ResponsePreviewConvertPoints
)
from app.services.wallet_service import WalletService

router = APIRouter(
    prefix="/wallet",
    tags=["wallet"],
)


# @router.get("/user/{externalUserId}", response_model=BaseWallet)
# @inject
# async def get_wallet_by_user_id(
#     externalUserId: str,
#     wallet_service: WalletService = Depends(Provide[Container.wallet_service]),
# ):
#     return wallet_service.get_wallet_by_user_id(externalUserId)


# @router.post("/previewConvert", response_model=ResponsePreviewConvertPoints)
# @inject
# async def preview_convert_points_to_coins(
#     schema: PostPreviewConvertPoints,
#     wallet_service: WalletService = Depends(Provide[Container.wallet_service]),
# ):
#     return wallet_service.preview_convert(schema)


# @router.post("/convert", response_model=bool)
# @inject
# async def convert_points_to_coins(
#     wallet: BaseWallet,
#     wallet_service: WalletService = Depends(Provide[Container.wallet_service]),
# ):
#     return True
#     # return wallet_service.convert(wallet)

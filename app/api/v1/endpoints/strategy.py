from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.strategy_schema import (
    FindStrategyResult
)
from app.schema.base_schema import FindBase
from app.services.strategy_service import StrategyService

router = APIRouter(
    prefix="/strategy",
    tags=["strategy"],
)


@router.get("/", response_model=FindStrategyResult)
@inject
def get_strategy_list(
    schema: FindBase = Depends(),
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    return service.get_list(schema)

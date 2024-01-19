from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.strategy_schema import (
    FindAllStrategyResult,
    FindStrategyResult,
    CreateStrategyPost,
    CreateStrategyResult
)
from app.schema.base_schema import FindBase
from app.services.strategy_service import StrategyService

router = APIRouter(
    prefix="/strategy",
    tags=["strategy"],
)


@router.get("/", response_model=FindAllStrategyResult)
@inject
def get_strategy_list(
    schema: FindBase = Depends(),
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    return service.get_list(schema)


@router.get("/{strategyName}", response_model=FindStrategyResult)
@inject
def get_strategy_by_strategyName(
    strategyName: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    return service.get_strategy_by_strategyName(strategyName)


@router.post("/", response_model=CreateStrategyResult)
@inject
def create_strategy(
    schema: CreateStrategyPost,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    return service.create_strategy(schema)

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from typing import List
from app.core.container import Container
from app.core.exceptions import NotFoundError
from app.schema.base_schema import FindBase
from app.schema.rules_schema import ResponseFindAllRuleVariables
from app.schema.strategy_schema import (
    Strategy,
    FindStrategyResult)
from app.services.strategy_service import StrategyService

router = APIRouter(
    prefix="/strategies",
    tags=["strategies"],
)

summary_get_strategies_list = "Get Strategies List"
description_get_strategies_list = """
## Find Strategy
### Find all strategies
"""


@router.get(
    "",
    response_model=List[Strategy],
    summary=summary_get_strategies_list,
    description=description_get_strategies_list,
)
@inject
def get_strategy_list(
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    response = service.list_all_strategies()
    return response


summary_get_strategy_by_id = "Get Strategy by id"
description_get_strategy_by_id = """
Get Strategy by id
"""


@router.get("/{id}", response_model=Strategy)
@inject
def get_strategy_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    all_strategies = service.list_all_strategies()
    for strategy in all_strategies:
        if strategy["id"] == id:
            return strategy
    raise NotFoundError(
        detail=f"Strategy not found with id: {id}"
    )

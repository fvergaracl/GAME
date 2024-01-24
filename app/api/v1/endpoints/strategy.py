from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.strategy_schema import (
    FindAllStrategyResult,
    FindStrategyResult,
    CreateStrategyPost,
    CreateStrategyResult
)

from app.schema.rules_schema import (
    ResponseFindAllRuleVariables
)
from app.schema.base_schema import FindBase
from app.services.strategy_service import StrategyService
from app.services.rules_service import RulesService

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
    service_rules: RulesService = Depends(Provide[Container.rules_service]),

):
    all_variables = service_rules.get_all_variables()
    all_variables = [variable.get_data() for variable in all_variables]
    return service.create_strategy(schema)


@router.get("/rules/variable", response_model=ResponseFindAllRuleVariables)
@inject
def get_variables_available_to_strategy(
    service: RulesService = Depends(Provide[Container.rules_service]),
):
    all_variables = service.get_all_variables()
    all_variables = [variable.get_data() for variable in all_variables]
    response = {
        "items": all_variables
    }
    return response

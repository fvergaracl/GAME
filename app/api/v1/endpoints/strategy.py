from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from typing import List
from app.core.container import Container
from app.schema.base_schema import FindBase
from app.schema.rules_schema import ResponseFindAllRuleVariables
from app.schema.strategy_schema import (CreateStrategyPost,
                                        CreateStrategyResult,
                                        Strategy,
                                        FindStrategyResult)
from app.services.rules_service import RulesService
from app.services.strategy_service import StrategyService

router = APIRouter(
    prefix="/strategies",
    tags=["strategies"],
)

# array of Strategy <- response model is an array of Strategy


@router.get("", response_model=List[Strategy])
@inject
def get_strategy_list(
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    response = service.list_all_strategies()
    return response


# @router.get("{id}", response_model=FindStrategyResult)
# @inject
# def get_strategy_by_id(
#     id: str,
#     service: StrategyService = Depends(Provide[Container.strategy_service]),
# ):
#     return service.get_strategy_by_id(id)


# @router.post("", response_model=CreateStrategyResult)
# @inject
# def create_strategy(
#     schema: CreateStrategyPost,
#     service: StrategyService = Depends(Provide[Container.strategy_service]),
#     service_rules: RulesService = Depends(Provide[Container.rules_service]),
# ):
#     all_variables = service_rules.get_all_variables()
#     all_variables = [variable.get_data() for variable in all_variables]
#     return service.create_strategy(schema)


# @router.get("rules/variable", response_model=ResponseFindAllRuleVariables)
# @inject
# def get_variables_available_to_strategy(
#     service: RulesService = Depends(Provide[Container.rules_service]),
# ):
#     all_variables = service.get_all_variables()
#     all_variables = [variable.get_data() for variable in all_variables]
#     response = {"items": all_variables}
#     return response

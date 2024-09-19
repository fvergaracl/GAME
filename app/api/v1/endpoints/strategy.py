from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.core.container import Container
from app.core.exceptions import NotFoundError
from app.schema.strategy_schema import Strategy
from app.services.strategy_service import StrategyService
import io

router = APIRouter(
    prefix="/strategies",
    tags=["strategies"],
)

summary_get_strategies_list = "Retrieve Strategies List"
description_get_strategies_list = """
## Retrieve Strategies List
### This endpoint retrieves a list of all available strategies.
<sub>**Id_endpoint:** get_strategy_list</sub>"""


@router.get(
    "",
    response_model=List[Strategy],
    summary=summary_get_strategies_list,
    description=description_get_strategies_list,
)
@inject
async def get_strategy_list(
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    """
    Retrieve a list of all strategies.

    Args:
        service (StrategyService): Injected StrategyService dependency.

    Returns:
        List[Strategy]: The list of all strategies.
    """

    response = service.list_all_strategies()
    return response


summary_get_strategy_by_id = "Retrieve Strategy by ID"
description_get_strategy_by_id = """
## Retrieve Strategy by ID
### This endpoint retrieves the details of a strategy using its unique ID. 
<sub>**Id_endpoint:** get_strategy_by_id</sub>"""


@router.get(
    "/{id}",
    response_model=Strategy,
    summary=summary_get_strategy_by_id,
    description=description_get_strategy_by_id,
)
@inject
def get_strategy_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    """
    Retrieve a strategy by its ID.

    Args:
        id (str): The ID of the strategy.
        service (StrategyService): Injected StrategyService dependency.

    Returns:
        Strategy: The details of the specified strategy.
    """
    all_strategies = service.list_all_strategies()
    for strategy in all_strategies:
        if strategy["id"] == id:
            return strategy
    raise NotFoundError(detail=f"Strategy not found with id: {id}")


summary_get_strategy_graph_by_id = "Retrieve Strategy Graph by ID"
description_get_strategy_graph_by_id = """
## Retrieve Strategy Graph by ID
### This endpoint retrieves the logic graph of a strategy using its unique ID.
<sub>**Id_endpoint:** get_strategy_graph_by_id</sub>"""


@router.get(
    "/{id}/graph",
    summary=summary_get_strategy_graph_by_id,
    description=description_get_strategy_graph_by_id,
)
@inject
def get_strategy_graph_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
):
    """
    Retrieve a strategy graph by its ID.

    Args:
        id (str): The ID of the strategy.
        service (StrategyService): Injected StrategyService dependency.

    Returns:
        StreamingResponse: The logic graph of the specified strategy.
    """
    strategy = service.get_strategy_by_id(id)

    if not strategy:
        raise NotFoundError(detail=f"Strategy not found with id: {id}")
    print(strategy)
    strategy_class = service.get_Class_by_id(id)
    if strategy_class is None:
        raise NotFoundError(
            detail=f"No class found for strategy with id: {id}")
    dot = strategy_class.generate_logic_graph(format="png")

    graph_png = dot.pipe(format="png")

    return StreamingResponse(io.BytesIO(graph_png), media_type="image/png")

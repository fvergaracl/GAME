from typing import List

from fastapi import APIRouter
from starlette.routing import BaseRoute

from app.api.v1.endpoints.apikey import router as apikey_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.games import router as game_router
from app.api.v1.endpoints.kpi import router as kpi_router
from app.api.v1.endpoints.strategies_custom import router as strategies_custom_router
from app.api.v1.endpoints.strategy import router as strategy_router
from app.api.v1.endpoints.strategy_observability import (
    router as strategy_observability_router,
)
from app.api.v1.endpoints.tasks import router as task_router
from app.api.v1.endpoints.userPoints import router as user_points_router
from app.api.v1.endpoints.users import router as user_router
from app.api.v1.endpoints.wallet import router as wallet_router

routers = APIRouter()
router_list = [
    apikey_router,
    # The observability router shares the
    # ``/strategies/custom`` prefix with strategies_custom_router and
    # owns a literal ``/compare`` path. FastAPI matches routes in
    # include-order, so this router has to come first - otherwise the
    # ``/{id}`` route on strategies_custom_router would swallow
    # ``/compare`` and 404 with "Custom strategy not found: compare".
    strategy_observability_router,
    strategies_custom_router,
    strategy_router,
    game_router,
    task_router,
    user_points_router,
    user_router,
    wallet_router,
    kpi_router,
    dashboard_router,
    exports_router,
]


for router in router_list:
    # router.tags = routers.tags.append("v1")
    routers.include_router(router)


def routes() -> List[BaseRoute]:
    """
    Returns the list of routes for the API v1.


    :return: List[BaseRoute]: The list of routes for the API v1.
    """
    return routers.routes

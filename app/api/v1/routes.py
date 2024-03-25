from typing import List
from fastapi import APIRouter

from app.api.v1.endpoints.games import router as game_router
from app.api.v1.endpoints.strategy import router as strategy_router
from app.api.v1.endpoints.tasks import router as task_router
from app.api.v1.endpoints.userPoints import router as user_points_router
from app.api.v1.endpoints.users import router as user_router
from app.api.v1.endpoints.wallet import router as wallet_router
from starlette.routing import BaseRoute

routers = APIRouter()
router_list = [
    strategy_router,
    game_router,
    task_router,
    user_points_router,
    user_router,
    wallet_router,
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

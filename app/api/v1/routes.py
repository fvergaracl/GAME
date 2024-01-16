from fastapi import APIRouter

from app.api.v1.endpoints.games import router as game_router

routers = APIRouter()
router_list = [game_router]

for router in router_list:
    router.tags = routers.tags.append("v1")
    routers.include_router(router)

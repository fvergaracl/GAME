from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.schema.user_points_schema import (
    FindQueryByExternalGameId,
    FindAllUserPointsResult,

)
from app.services.user_points_service import UserPointsService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

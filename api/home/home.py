from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from core.fastapi.dependencies import PermissionDependency, AllowAll

home_router = APIRouter()


@home_router.get("/health", dependencies=[Depends(PermissionDependency([AllowAll]))])
async def home():
    json_response = {"GAME": "Goals And Motivation Engine" , "version": "0.0.1"}
    return JSONResponse(
        status_code=200,
        content=json_response
    )
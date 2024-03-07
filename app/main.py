from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import subprocess
import toml
from app.api.v1.routes import routers as v1_routers
from app.core.config import configs
from app.core.container import Container
from app.util.class_object import singleton
from fastapi.openapi.utils import get_openapi
from app.schema.base_schema import RootEndpoint
from fastapi.responses import RedirectResponse


def get_project_data():
    # Asegúrate de que la ruta sea accesible desde tu script
    pyproject_path = "pyproject.toml"
    with open(pyproject_path, "r") as pyproject_file:
        pyproject_content = toml.load(pyproject_file)
    return pyproject_content['tool']['poetry']


project_data = get_project_data()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=project_data['name'],
        version=project_data['version'],
        description=project_data['description'],
        routes=app.routes,
        servers=[{"url": "/api/v1", "description": "Local"}]
    )
    # Eliminar el prefijo /api/v1 de las rutas en la documentación de Swagger
    for path in list(openapi_schema["paths"].keys()):
        print(path)
        if path.startswith("/api/v1"):
            openapi_schema["paths"][path[7:]
                                    ] = openapi_schema["paths"].pop(path)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_git_commit_hash() -> str:
    """
    Returns the current git commit hash, or "unknown" if not available. 
    """
    try:

        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    except Exception:
        commit_hash = "unknown"
    return commit_hash


@singleton
class AppCreator:
    def __init__(self):
        # set app default
        self.app = FastAPI(
            redoc_url="/redocs",
            docs_url="/docs",
            servers=[{"url": configs.API_V1_STR, "description": "Local"}]
        )
        self.app.openapi = custom_openapi

        # set db and container
        self.container = Container()
        self.db = self.container.db()
        # self.db.create_database()

        # set cors
        if configs.BACKEND_CORS_ORIGINS:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=[str(origin)
                               for origin in configs.BACKEND_CORS_ORIGINS],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        @self.app.get("/", include_in_schema=False)
        def read_root():
            """
            Redirect to /docs

            return:
                RedirectResponse: Redirect to /docs
            """
            return RedirectResponse(url='/docs')

        # set routes

        @self.app.get(
            "/api/v1",
            tags=["root"],
            response_model=RootEndpoint,
            summary="Root API v1 endpoint",
            description="General information about the API"
        )
        def root():
            """
            Root API v1 endpoint

            return:
                RootEndpoint: General information about the API
            """
            version = configs.GAMIFICATIONENGINE_VERSION_APP
            project_name = configs.PROJECT_NAME
            return {
                "projectName": project_name,
                "version": version,
                "message": "Welcome to GAME API",
                "docs": "/docs",
                "redocs": "/redocs",
                "commitVersion": get_git_commit_hash()
            }

        # set routers API_V1_STR

        # self.app.include_router(v1_routers)
        self.app.include_router(v1_routers, prefix=configs.API_V1_STR)


app_creator = AppCreator()
app = app_creator.app
db = app_creator.db
container = app_creator.container

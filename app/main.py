import subprocess

import sentry_sdk
import toml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.routes import routers as v1_routers
from app.core.config import configs
from app.core.container import Container
from app.util.class_object import singleton


def get_project_data():
    """
    Retrieves project data from the pyproject.toml file.

    Returns:
        dict: Project data from the toml file.
    """
    pyproject_path = "pyproject.toml"
    with open(pyproject_path, "r") as pyproject_file:
        pyproject_content = toml.load(pyproject_file)
    return pyproject_content["tool"]["poetry"]


project_data = get_project_data()


def get_swagger_oauth_config() -> dict:
    """
    Builds Swagger UI OAuth init configuration from environment-based settings.

    Returns:
        dict: Swagger OAuth init configuration.
    """
    oauth_config = {}
    if configs.KEYCLOAK_CLIENT_ID:
        oauth_config["clientId"] = configs.KEYCLOAK_CLIENT_ID
    if configs.KEYCLOAK_CLIENT_SECRET:
        oauth_config["clientSecret"] = configs.KEYCLOAK_CLIENT_SECRET
    return oauth_config


def custom_openapi():
    """
    Customizes the OpenAPI schema for the FastAPI application.

    Returns:
        dict: The customized OpenAPI schema.
    """
    servers = [{"url": configs.API_V1_STR, "description": "Local"}]

    extra_server_url = configs.EXTRA_SERVER_URL
    extra_server_description = configs.EXTRA_SERVER_DESCRIPTION

    if extra_server_url:
        servers.append(
            {"url": extra_server_url, "description": extra_server_description}
        )

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=project_data["name"],
        version=project_data["version"],
        description=project_data["description"],
        routes=app.routes,
        servers=servers,
    )
    for path in list(openapi_schema["paths"].keys()):

        if path.startswith("/api/v1"):
            openapi_schema["paths"][path[7:]] = openapi_schema["paths"].pop(path)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_git_commit_hash() -> str:
    """
    Returns the current git commit hash, or "unknown" if not available.

    Returns:
        str: The current git commit hash, or "unknown" if not available.
    """
    try:

        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()
        )
    except Exception:
        commit_hash = "unknown"
    return commit_hash


@singleton
class AppCreator:
    """
    Singleton class to create and configure the FastAPI application.
    """

    def __init__(self):

        if configs.SENTRY_DSN:
            sentry_sdk.init(
                dsn=configs.SENTRY_DSN,
                environment=configs.SENTRY_ENVIRONMENT,
                release=configs.SENTRY_RELEASE,
                send_default_pii=True,
                traces_sample_rate=1.0,
                _experiments={
                    "continuous_profiling_auto_start": True,
                },
            )

        self.app = FastAPI(
            root_path=configs.ROOT_PATH,
            title=project_data["name"],
            version=project_data["version"],
            description=project_data["description"],
            license_info={"name": project_data["license"]},
            contact={
                "name": project_data["authors"][0],
                "email": project_data["authors"][0],
            },
            redoc_url="/redocs",
            docs_url="/docs",
            servers=[{"url": configs.API_V1_STR, "description": "Local"}],
            swagger_ui_init_oauth=get_swagger_oauth_config(),
        )

        self.app.openapi = custom_openapi

        self.container = Container()
        self.db = self.container.db()
        if configs.BACKEND_CORS_ORIGINS:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=[str(origin) for origin in configs.BACKEND_CORS_ORIGINS],
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
            return RedirectResponse(url="/docs")

        self.app.include_router(v1_routers, prefix=configs.API_V1_STR)


app_creator = AppCreator()
app = app_creator.app
db = app_creator.db
container = app_creator.container

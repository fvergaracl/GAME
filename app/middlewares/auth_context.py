from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, Request

from app.core.container import Container
from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.schema.oauth_users_schema import CreateOAuthUser
from app.services.apikey_service import ApiKeyService
from app.services.logs_service import LogsService
from app.services.oauth_users_service import OAuthUsersService
from app.util.add_log import add_log
from app.util.check_role import check_role


@dataclass(frozen=True)
class AuthContext:
    """Per-request auth context resolved by `get_auth_context`."""

    api_key: Optional[str]
    oauth_user_id: Optional[str]
    is_admin: bool
    token_data: Optional[Dict[str, Any]]


class AuditLogger:
    """Per-request audit logger bound to a module name and AuthContext."""

    def __init__(self, module: str, service_log: LogsService, auth: AuthContext):
        self.module = module
        self.service_log = service_log
        self.auth = auth

    async def info(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        await add_log(
            self.module,
            "INFO",
            message,
            details or {},
            self.service_log,
            api_key=self.auth.api_key,
            oauth_user_id=self.auth.oauth_user_id,
        )

    async def success(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        await add_log(
            self.module,
            "SUCCESS",
            message,
            details or {},
            self.service_log,
            api_key=self.auth.api_key,
            oauth_user_id=self.auth.oauth_user_id,
        )

    async def error(
        self, message: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        await add_log(
            self.module,
            "ERROR",
            message,
            details or {},
            self.service_log,
            api_key=self.auth.api_key,
            oauth_user_id=self.auth.oauth_user_id,
        )


@inject
async def get_auth_context(
    request: Request,  # noqa: ARG001 - reserved for request-scoped metadata
    token: Optional[str] = Depends(oauth_2_scheme),
    api_key_header=Depends(ApiKeyService.get_api_key_header),
    service_oauth: OAuthUsersService = Depends(Provide[Container.oauth_users_service]),
    service_log: LogsService = Depends(Provide[Container.logs_service]),
) -> AuthContext:
    """
    Resolves the per-request auth context from `Authorization: Bearer`
      and/or `X-API-Key`.

    When a bearer token is present:
      - validates it via `valid_access_token`,
      - extracts `sub` and admin role,
      - bootstraps a Keycloak OAuth user record if missing (and writes a
        single `auth / OAuth user bootstrapped` audit entry).
    """
    api_key = getattr(getattr(api_key_header, "data", None), "apiKey", None)
    oauth_user_id: Optional[str] = None
    is_admin = False
    token_data: Optional[Dict[str, Any]] = None

    if token:
        validated = await valid_access_token(token)
        if validated.error:
            raise validated.error
        token_data = validated.data
        oauth_user_id = token_data["sub"]
        is_admin = check_role(token_data, "AdministratorGAME")
        if await service_oauth.get_user_by_sub(oauth_user_id) is None:
            await service_oauth.add(
                CreateOAuthUser(
                    provider="keycloak",
                    provider_user_id=oauth_user_id,
                    status="active",
                )
            )
            await add_log(
                "auth",
                "INFO",
                "OAuth user bootstrapped",
                {"oauth_user_id": oauth_user_id},
                service_log,
                api_key=api_key,
                oauth_user_id=oauth_user_id,
            )

    return AuthContext(
        api_key=api_key,
        oauth_user_id=oauth_user_id,
        is_admin=is_admin,
        token_data=token_data,
    )


def audit_log(module: str) -> Callable:
    """
    Factory that returns a FastAPI dependency yielding an `AuditLogger`
      pre-bound to `module` and the resolved `AuthContext`.

    Usage:

        @router.get("/foo", dependencies=[Depends(auth_api_key_or_oauth2)])
        async def foo(
            audit: AuditLogger = Depends(audit_log("users")),
        ):
            await audit.info("Foo invoked", {...})
            try:
                ...
            except Exception as e:
                await audit.error("Foo failed", {"error": str(e)})
                raise
    """

    @inject
    async def _audit_log_dependency(
        request: Request,  # noqa: ARG001 - kept for future per-request metadata
        auth: AuthContext = Depends(get_auth_context),
        service_log: LogsService = Depends(Provide[Container.logs_service]),
    ) -> AuditLogger:
        return AuditLogger(module, service_log, auth)

    return _audit_log_dependency

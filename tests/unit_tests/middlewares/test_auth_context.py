from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middlewares.auth_context import AuditLogger, get_auth_context


def _api_key_header(api_key="api-key-1"):
    return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))


@pytest.mark.asyncio
async def test_get_auth_context_bootstraps_missing_oauth_user_and_logs():
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(return_value=None)
    service_oauth.add = AsyncMock()
    token_response = SimpleNamespace(
        error=None,
        data={"sub": "oauth-user-1"},
    )

    with patch(
        "app.middlewares.auth_context.valid_access_token",
        new=AsyncMock(return_value=token_response),
    ), patch("app.middlewares.auth_context.check_role", return_value=True), patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        auth = await get_auth_context(
            request=MagicMock(),
            token="Bearer token",
            api_key_header=_api_key_header("k-1"),
            service_oauth=service_oauth,
            service_log=MagicMock(),
        )

    assert auth.api_key == "k-1"
    assert auth.oauth_user_id == "oauth-user-1"
    assert auth.is_admin is True
    assert auth.token_data == {"sub": "oauth-user-1"}
    service_oauth.add.assert_awaited_once()
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_auth_context_skips_bootstrap_when_user_exists():
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(
        return_value=SimpleNamespace(id="existing")
    )
    service_oauth.add = AsyncMock()
    token_response = SimpleNamespace(
        error=None,
        data={"sub": "oauth-user-1"},
    )

    with patch(
        "app.middlewares.auth_context.valid_access_token",
        new=AsyncMock(return_value=token_response),
    ), patch("app.middlewares.auth_context.check_role", return_value=False), patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        auth = await get_auth_context(
            request=MagicMock(),
            token="Bearer token",
            api_key_header=_api_key_header("k-1"),
            service_oauth=service_oauth,
            service_log=MagicMock(),
        )

    assert auth.oauth_user_id == "oauth-user-1"
    assert auth.is_admin is False
    service_oauth.add.assert_not_called()
    mock_add_log.assert_not_called()


@pytest.mark.asyncio
async def test_get_auth_context_api_key_only_skips_token_path():
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock()
    service_oauth.add = AsyncMock()

    with patch(
        "app.middlewares.auth_context.valid_access_token", new=AsyncMock()
    ) as mock_validate, patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        auth = await get_auth_context(
            request=MagicMock(),
            token=None,
            api_key_header=_api_key_header("only-api-key"),
            service_oauth=service_oauth,
            service_log=MagicMock(),
        )

    assert auth.api_key == "only-api-key"
    assert auth.oauth_user_id is None
    assert auth.is_admin is False
    assert auth.token_data is None
    mock_validate.assert_not_called()
    service_oauth.get_user_by_sub.assert_not_called()
    service_oauth.add.assert_not_called()
    mock_add_log.assert_not_called()


@pytest.mark.asyncio
async def test_get_auth_context_raises_token_error():
    token_error = RuntimeError("bad token")
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock()

    with patch(
        "app.middlewares.auth_context.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=token_error, data=None)),
    ):
        with pytest.raises(RuntimeError, match="bad token"):
            await get_auth_context(
                request=MagicMock(),
                token="Bearer token",
                api_key_header=_api_key_header(),
                service_oauth=service_oauth,
                service_log=MagicMock(),
            )

    service_oauth.get_user_by_sub.assert_not_called()


@pytest.mark.asyncio
async def test_audit_logger_methods_route_to_add_log_with_bound_context():
    from app.middlewares.auth_context import AuthContext

    auth = AuthContext(
        api_key="k-1",
        oauth_user_id="user-1",
        is_admin=False,
        token_data={"sub": "user-1"},
    )
    service_log = MagicMock()
    logger = AuditLogger("users", service_log, auth)

    with patch(
        "app.middlewares.auth_context.add_log", new=AsyncMock()
    ) as mock_add_log:
        await logger.info("op", {"k": "v"})
        await logger.success("ok", {"id": 1})
        await logger.error("boom", {"error": "x"})

    assert mock_add_log.await_count == 3
    levels = [call.args[1] for call in mock_add_log.await_args_list]
    assert levels == ["INFO", "SUCCESS", "ERROR"]
    for call in mock_add_log.await_args_list:
        assert call.kwargs == {"api_key": "k-1", "oauth_user_id": "user-1"}
        assert call.args[0] == "users"

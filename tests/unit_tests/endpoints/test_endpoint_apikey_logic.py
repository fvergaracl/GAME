from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import apikey as apikey_endpoint
from app.core.exceptions import ForbiddenError
from app.schema.apikey_schema import ApiKeyPostBody


class _FakeApiKeyCreated:
    def dict(self):
        return {
            "apiKey": "generated-key",
            "client": "client-a",
            "description": "desc-a",
            "createdBy": "oauth-user-1",
        }


def _api_key_header(api_key="api-key-header-1"):
    return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))


@pytest.mark.asyncio
async def test_create_api_key_raises_when_token_validation_fails():
    service = MagicMock()
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=RuntimeError("bad-token"), data=None)),
    ), patch("app.api.v1.endpoints.apikey.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(RuntimeError, match="bad-token"):
            await apikey_endpoint.create_api_key(
                schema=ApiKeyPostBody(client="client-a", description="desc-a"),
                service=service,
                service_log=service_log,
                service_oauth=service_oauth,
                token="Bearer token",
                api_key_header=_api_key_header(),
            )

    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_api_key_raises_forbidden_when_role_is_missing():
    service = MagicMock()
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(return_value=SimpleNamespace(id="oauth-user-1"))

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-1"})),
    ), patch("app.api.v1.endpoints.apikey.check_role", return_value=False), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ) as mock_add_log:
        with pytest.raises(ForbiddenError):
            await apikey_endpoint.create_api_key(
                schema=ApiKeyPostBody(client="client-a", description="desc-a"),
                service=service,
                service_log=service_log,
                service_oauth=service_oauth,
                token="Bearer token",
                api_key_header=_api_key_header(),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_create_api_key_logs_and_raises_when_create_fails():
    service = MagicMock()
    service.generate_api_key_service = AsyncMock(return_value="generated-key")
    service.create_api_key = AsyncMock(side_effect=RuntimeError("db-failure"))
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(return_value=SimpleNamespace(id="oauth-user-1"))

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-1"})),
    ), patch("app.api.v1.endpoints.apikey.check_role", return_value=True), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ) as mock_add_log:
        with pytest.raises(RuntimeError, match="db-failure"):
            await apikey_endpoint.create_api_key(
                schema=ApiKeyPostBody(client="client-a", description="desc-a"),
                service=service,
                service_log=service_log,
                service_oauth=service_oauth,
                token="Bearer token",
                api_key_header=_api_key_header(),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_all_api_keys_raises_when_token_validation_fails():
    service = MagicMock()
    service_log = MagicMock()
    service_oauth = MagicMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=RuntimeError("bad-token"), data=None)),
    ), patch("app.api.v1.endpoints.apikey.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(RuntimeError, match="bad-token"):
            await apikey_endpoint.get_all_api_keys(
                service=service,
                service_log=service_log,
                service_oauth=service_oauth,
                token="Bearer token",
                api_key_header=_api_key_header(),
            )

    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_api_keys_raises_forbidden_when_role_is_missing():
    service = MagicMock()
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = MagicMock(return_value=SimpleNamespace(id="oauth-user-1"))
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-1"})),
    ), patch("app.api.v1.endpoints.apikey.check_role", return_value=False), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ) as mock_add_log:
        with pytest.raises(ForbiddenError):
            await apikey_endpoint.get_all_api_keys(
                service=service,
                service_log=service_log,
                service_oauth=service_oauth,
                token="Bearer token",
                api_key_header=_api_key_header(),
            )

    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_api_keys_success_creates_missing_user_and_returns_data():
    service = MagicMock()
    expected = [{"apiKey": "k-1"}, {"apiKey": "k-2"}]
    service.get_all_api_keys = MagicMock(return_value=expected)
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = MagicMock(return_value=None)
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-2"})),
    ), patch("app.api.v1.endpoints.apikey.check_role", return_value=True), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ) as mock_add_log:
        result = await apikey_endpoint.get_all_api_keys(
            service=service,
            service_log=service_log,
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert result == expected
    service_oauth.add.assert_awaited_once()
    service.get_all_api_keys.assert_called_once()
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_create_api_key_success_creates_missing_user_and_returns_response_model():
    service = MagicMock()
    service.generate_api_key_service = AsyncMock(return_value="generated-key")
    service.create_api_key = AsyncMock(return_value=_FakeApiKeyCreated())
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(return_value=None)
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-1"})),
    ), patch("app.api.v1.endpoints.apikey.check_role", return_value=True), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ) as mock_add_log:
        result = await apikey_endpoint.create_api_key(
            schema=ApiKeyPostBody(client="client-a", description="desc-a"),
            service=service,
            service_log=service_log,
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert result.message == "API Key created successfully"
    assert result.apiKey == "generated-key"
    assert result.createdBy == "oauth-user-1"
    service_oauth.add.assert_awaited_once()
    service.generate_api_key_service.assert_awaited_once()
    service.create_api_key.assert_awaited_once()
    assert mock_add_log.await_count == 3

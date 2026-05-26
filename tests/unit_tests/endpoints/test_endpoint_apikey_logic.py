from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import apikey as apikey_endpoint
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schema.apikey_schema import ApiKeyPostBody
from app.util.generate_api_key import GeneratedApiKey


GENERATED = GeneratedApiKey(
    plaintext="gme_live_generat.SECRET-SECRET-SECRET-SECRET-SECRE",
    prefix="gme_live_generat",
    key_hash="deadbeef" * 8,
)


class _FakeApiKeyCreated:
    def model_dump(self):
        return {
            "apiKey": GENERATED.prefix,
            "apiKeyHash": GENERATED.key_hash,
            "client": "client-a",
            "description": "desc-a",
            "createdBy": "oauth-user-1",
        }


def _api_key_header(api_key="api-key-header-1"):
    return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))


@pytest.mark.asyncio
async def test_create_api_key_raises_when_token_validation_fails():
    service = AsyncMock()
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=RuntimeError("bad-token"), data=None
        )),
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
    service = AsyncMock()
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(
        return_value=SimpleNamespace(id="oauth-user-1")
    )

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-1"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=False
    ), patch(
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
    service = AsyncMock()
    service.generate_api_key_service = AsyncMock(return_value=GENERATED)
    service.create_api_key = AsyncMock(side_effect=RuntimeError("db-failure"))
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(
        return_value=SimpleNamespace(id="oauth-user-1")
    )

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-1"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=True
    ), patch(
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
    service = AsyncMock()
    service_log = MagicMock()
    service_oauth = MagicMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=RuntimeError("bad-token"), data=None
        )),
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
    service = AsyncMock()
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(
        return_value=SimpleNamespace(id="oauth-user-1")
    )
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-1"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=False
    ), patch(
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
    service = AsyncMock()
    expected = [{"apiKey": "k-1"}, {"apiKey": "k-2"}]
    service.get_all_api_keys = AsyncMock(return_value=expected)
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(return_value=None)
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-2"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=True
    ), patch(
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
async def test_create_api_key_success_returns_plaintext_only_once():
    service = AsyncMock()
    service.generate_api_key_service = AsyncMock(return_value=GENERATED)
    service.create_api_key = AsyncMock(return_value=_FakeApiKeyCreated())
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(return_value=None)
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-1"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=True
    ), patch(
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
    # Public prefix surfaces in `apiKey`, plaintext in `plaintext`.
    assert result.apiKey == GENERATED.prefix
    assert result.plaintext == GENERATED.plaintext
    assert result.createdBy == "oauth-user-1"
    service_oauth.add.assert_awaited_once()
    service.generate_api_key_service.assert_awaited_once()
    service.create_api_key.assert_awaited_once()
    assert mock_add_log.await_count == 3


@pytest.mark.asyncio
async def test_revoke_api_key_success_returns_revoked_payload():
    service = AsyncMock()
    service.revoke_api_key_by_prefix = AsyncMock(
        return_value=SimpleNamespace(
            apiKey="gme_live_revoked0", active=False
        )
    )
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(
        return_value=SimpleNamespace(id="oauth-user-admin")
    )
    service_oauth.add = AsyncMock()

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-admin"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=True
    ), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ) as mock_add_log:
        result = await apikey_endpoint.revoke_api_key(
            prefix="gme_live_revoked0",
            service=service,
            service_log=service_log,
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert result.apiKey == "gme_live_revoked0"
    assert result.active is False
    assert result.message == "API key revoked successfully."
    service.revoke_api_key_by_prefix.assert_called_once_with(
        "gme_live_revoked0"
    )
    mock_add_log.assert_awaited()


@pytest.mark.asyncio
async def test_revoke_api_key_forbids_non_admin():
    service = AsyncMock()
    service.revoke_api_key_by_prefix = AsyncMock()
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(
        return_value=SimpleNamespace(id="oauth-user-non-admin")
    )

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-non-admin"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=False
    ), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ):
        with pytest.raises(ForbiddenError):
            await apikey_endpoint.revoke_api_key(
                prefix="gme_live_revoked0",
                service=service,
                service_log=service_log,
                service_oauth=service_oauth,
                token="Bearer token",
                api_key_header=_api_key_header(),
            )

    service.revoke_api_key_by_prefix.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_api_key_raises_not_found_when_prefix_missing():
    service = AsyncMock()
    service.revoke_api_key_by_prefix = AsyncMock(
        side_effect=NotFoundError("missing")
    )
    service_log = MagicMock()
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub = AsyncMock(
        return_value=SimpleNamespace(id="oauth-user-admin")
    )

    with patch(
        "app.api.v1.endpoints.apikey.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(
            error=None, data={"sub": "oauth-user-admin"}
        )),
    ), patch(
        "app.api.v1.endpoints.apikey.check_role", return_value=True
    ), patch(
        "app.api.v1.endpoints.apikey.add_log", new=AsyncMock()
    ):
        with pytest.raises(NotFoundError):
            await apikey_endpoint.revoke_api_key(
                prefix="gme_live_missing0",
                service=service,
                service_log=service_log,
                service_oauth=service_oauth,
                token="Bearer token",
                api_key_header=_api_key_header(),
            )

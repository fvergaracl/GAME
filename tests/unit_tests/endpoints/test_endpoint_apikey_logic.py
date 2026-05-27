from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import apikey as apikey_endpoint
from app.core.exceptions import ForbiddenError, NotFoundError
from app.middlewares.auth_context import AuditLogger, AuthContext
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


def _audit(api_key="api-key-header-1", oauth_user_id="oauth-user-1", is_admin=True):
    return AuditLogger(
        "api_key",
        MagicMock(),
        AuthContext(
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=is_admin,
            token_data={"sub": oauth_user_id} if oauth_user_id else None,
        ),
    )


@pytest.mark.asyncio
async def test_create_api_key_raises_forbidden_when_role_is_missing():
    service = AsyncMock()

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(ForbiddenError):
            await apikey_endpoint.create_api_key(
                schema=ApiKeyPostBody(client="client-a", description="desc-a"),
                service=service,
                audit=_audit(is_admin=False),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_create_api_key_logs_and_raises_when_create_fails():
    service = AsyncMock()
    service.generate_api_key_service = AsyncMock(return_value=GENERATED)
    service.create_api_key = AsyncMock(side_effect=RuntimeError("db-failure"))

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(RuntimeError, match="db-failure"):
            await apikey_endpoint.create_api_key(
                schema=ApiKeyPostBody(client="client-a", description="desc-a"),
                service=service,
                audit=_audit(is_admin=True),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_all_api_keys_raises_forbidden_when_role_is_missing():
    service = AsyncMock()

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(ForbiddenError):
            await apikey_endpoint.get_all_api_keys(
                service=service,
                audit=_audit(is_admin=False),
            )

    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_all_api_keys_success_returns_data():
    service = AsyncMock()
    expected = [{"apiKey": "k-1"}, {"apiKey": "k-2"}]
    service.get_all_api_keys = AsyncMock(return_value=expected)

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await apikey_endpoint.get_all_api_keys(
            service=service,
            audit=_audit(oauth_user_id="oauth-user-2", is_admin=True),
        )

    assert result == expected
    service.get_all_api_keys.assert_called_once()
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_api_key_success_returns_plaintext_only_once():
    service = AsyncMock()
    service.generate_api_key_service = AsyncMock(return_value=GENERATED)
    service.create_api_key = AsyncMock(return_value=_FakeApiKeyCreated())

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await apikey_endpoint.create_api_key(
            schema=ApiKeyPostBody(client="client-a", description="desc-a"),
            service=service,
            audit=_audit(is_admin=True),
        )

    assert result.message == "API Key created successfully"
    # Public prefix surfaces in `apiKey`, plaintext in `plaintext`.
    assert result.apiKey == GENERATED.prefix
    assert result.plaintext == GENERATED.plaintext
    assert result.createdBy == "oauth-user-1"
    service.generate_api_key_service.assert_awaited_once()
    service.create_api_key.assert_awaited_once()
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_revoke_api_key_success_returns_revoked_payload():
    service = AsyncMock()
    service.revoke_api_key_by_prefix = AsyncMock(
        return_value=SimpleNamespace(apiKey="gme_live_revoked0", active=False)
    )

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await apikey_endpoint.revoke_api_key(
            prefix="gme_live_revoked0",
            service=service,
            audit=_audit(oauth_user_id="oauth-user-admin", is_admin=True),
        )

    assert result.apiKey == "gme_live_revoked0"
    assert result.active is False
    assert result.message == "API key revoked successfully."
    service.revoke_api_key_by_prefix.assert_called_once_with("gme_live_revoked0")
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_api_key_forbids_non_admin():
    service = AsyncMock()
    service.revoke_api_key_by_prefix = AsyncMock()

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        with pytest.raises(ForbiddenError):
            await apikey_endpoint.revoke_api_key(
                prefix="gme_live_revoked0",
                service=service,
                audit=_audit(oauth_user_id="oauth-user-non-admin", is_admin=False),
            )

    service.revoke_api_key_by_prefix.assert_not_called()


@pytest.mark.asyncio
async def test_revoke_api_key_raises_not_found_when_prefix_missing():
    service = AsyncMock()
    service.revoke_api_key_by_prefix = AsyncMock(side_effect=NotFoundError("missing"))

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        with pytest.raises(NotFoundError):
            await apikey_endpoint.revoke_api_key(
                prefix="gme_live_missing0",
                service=service,
                audit=_audit(oauth_user_id="oauth-user-admin", is_admin=True),
            )

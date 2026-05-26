from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import httpx
import jwt
import pytest
from fastapi import HTTPException
from jwt import exceptions

import app.middlewares.valid_access_token as access_token_middleware


@pytest.fixture(autouse=True)
def _reset_jwks_singleton():
    """Drop the cached PyJWKClient so each test sees the patched class."""
    access_token_middleware._reset_jwks_client_for_tests()
    yield
    access_token_middleware._reset_jwks_client_for_tests()


@pytest.mark.asyncio
async def test_custom_oauth2_bearer_returns_token_when_super_call_succeeds(monkeypatch):
    async def fake_super_call(self, request):
        return "token-value"

    monkeypatch.setattr(
        access_token_middleware.OAuth2AuthorizationCodeBearer,
        "__call__",
        fake_super_call,
    )
    scheme = access_token_middleware.CustomOAuth2AuthorizationCodeBearer(
        tokenUrl="https://example.com/token",
        authorizationUrl="https://example.com/auth",
    )

    result = await scheme(MagicMock())

    assert result == "token-value"


@pytest.mark.asyncio
async def test_custom_oauth2_bearer_returns_false_on_http_exception(monkeypatch):
    async def fake_super_call(self, request):
        raise HTTPException(status_code=401, detail="invalid credentials")

    monkeypatch.setattr(
        access_token_middleware.OAuth2AuthorizationCodeBearer,
        "__call__",
        fake_super_call,
    )
    scheme = access_token_middleware.CustomOAuth2AuthorizationCodeBearer(
        tokenUrl="https://example.com/token",
        authorizationUrl="https://example.com/auth",
    )

    result = await scheme(MagicMock())

    assert result is False


def _mock_jwks_client(monkeypatch, signing_key="public-key", side_effect=None):
    jwks_client = MagicMock()
    if side_effect is not None:
        jwks_client.get_signing_key_from_jwt.side_effect = side_effect
    else:
        jwks_client.get_signing_key_from_jwt.return_value = SimpleNamespace(
            key=signing_key
        )

    monkeypatch.setattr(
        access_token_middleware, "PyJWKClient", MagicMock(return_value=jwks_client)
    )
    return jwks_client


@pytest.mark.asyncio
async def test_valid_access_token_returns_ok_response_on_success(monkeypatch):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt, "decode", MagicMock(return_value={"sub": "user-1"})
    )

    result = await access_token_middleware.valid_access_token("valid-token")

    assert result.sucess is True
    assert result.data == {"sub": "user-1"}
    assert result.error is None


@pytest.mark.asyncio
async def test_valid_access_token_returns_fail_response_for_invalid_signature(
    monkeypatch,
):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=exceptions.InvalidSignatureError("bad signature")),
    )

    result = await access_token_middleware.valid_access_token("bad-token")

    assert result.sucess is False
    assert result.error.status_code == 401
    assert result.error.detail == "Invalid token signature"


@pytest.mark.asyncio
async def test_valid_access_token_rejects_expired_token(monkeypatch):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=exceptions.ExpiredSignatureError("expired")),
    )

    result = await access_token_middleware.valid_access_token("expired-token")

    assert result.sucess is False
    assert result.error.status_code == 401
    assert result.error.detail == "Token has expired"


@pytest.mark.asyncio
async def test_valid_access_token_passes_leeway_to_jwt_decode(monkeypatch):
    _mock_jwks_client(monkeypatch)
    decode_mock = MagicMock(return_value={"sub": "user-1"})
    monkeypatch.setattr(access_token_middleware.jwt, "decode", decode_mock)

    await access_token_middleware.valid_access_token("valid-token")

    _, kwargs = decode_mock.call_args
    assert kwargs.get("leeway") == 30
    assert kwargs["options"]["verify_exp"] is True
    assert kwargs["options"]["verify_aud"] is True
    assert kwargs.get("audience") == access_token_middleware.configs.KEYCLOAK_AUDIENCE


@pytest.mark.asyncio
async def test_valid_access_token_returns_fail_response_for_invalid_audience(
    monkeypatch,
):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=exceptions.InvalidAudienceError("invalid audience")),
    )

    result = await access_token_middleware.valid_access_token("token")

    assert result.sucess is False
    assert result.error.status_code == 403
    assert result.error.detail == "Invalid audience"


@pytest.mark.asyncio
async def test_valid_access_token_returns_fail_response_for_invalid_token(monkeypatch):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=exceptions.InvalidTokenError("invalid token")),
    )

    result = await access_token_middleware.valid_access_token("token")

    assert result.sucess is False
    assert result.error.status_code == 401
    assert result.error.detail == "Invalid token"


@pytest.mark.asyncio
async def test_valid_access_token_returns_fail_response_for_pyjwk_client_error(
    monkeypatch,
):
    _mock_jwks_client(monkeypatch, side_effect=exceptions.PyJWKClientError("jwks down"))

    result = await access_token_middleware.valid_access_token("token")

    assert result.sucess is False
    assert result.error.status_code == 500
    assert result.error.detail == "Internal server error"


@pytest.mark.asyncio
async def test_valid_access_token_returns_fail_response_for_generic_pyjwt_error(
    monkeypatch,
):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=jwt.PyJWTError("generic jwt error")),
    )

    result = await access_token_middleware.valid_access_token("token")

    assert result.sucess is False
    assert result.error.status_code == 401
    assert "Invalid token: generic jwt error" == result.error.detail


class _FakeAsyncClient:
    """Replacement for ``httpx.AsyncClient`` used by refresh_access_token tests."""

    post_mock: AsyncMock = AsyncMock()

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, data=None):
        return await type(self).post_mock(url, data=data)


def _install_fake_httpx(monkeypatch, post_side_effect):
    _FakeAsyncClient.post_mock = AsyncMock(side_effect=post_side_effect)
    monkeypatch.setattr(
        access_token_middleware.httpx, "AsyncClient", _FakeAsyncClient
    )
    return _FakeAsyncClient.post_mock


@pytest.mark.asyncio
async def test_refresh_access_token_returns_json_on_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"access_token": "new-token"}
    post_mock = _install_fake_httpx(monkeypatch, [mock_response])

    result = await access_token_middleware.refresh_access_token("refresh-token")

    assert result == {"access_token": "new-token"}
    post_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_access_token_raises_http_400_on_http_error(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad request",
        request=httpx.Request("POST", "http://example.com"),
        response=httpx.Response(400),
    )
    _install_fake_httpx(monkeypatch, [mock_response])

    with pytest.raises(HTTPException) as exc_info:
        await access_token_middleware.refresh_access_token("refresh-token")

    assert exc_info.value.status_code == 400
    assert "Failed to refresh token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_refresh_access_token_raises_http_500_on_unexpected_error(monkeypatch):
    _install_fake_httpx(monkeypatch, RuntimeError("service unavailable"))

    with pytest.raises(HTTPException) as exc_info:
        await access_token_middleware.refresh_access_token("refresh-token")

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail



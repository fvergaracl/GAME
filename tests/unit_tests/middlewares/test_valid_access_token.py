from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
import pytest
import requests
from fastapi import HTTPException
from jwt import exceptions

import app.middlewares.valid_access_token as access_token_middleware
from app.util.response import Response


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
        jwks_client.get_signing_key_from_jwt.return_value = SimpleNamespace(key=signing_key)

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
async def test_valid_access_token_returns_fail_response_for_invalid_signature(monkeypatch):
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
async def test_valid_access_token_uses_decode_without_exp_check_when_expired(monkeypatch):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=exceptions.ExpiredSignatureError("expired")),
    )
    decoded_response = Response.ok({"sub": "expired-user"})
    decode_without_exp_mock = MagicMock(return_value=decoded_response)
    monkeypatch.setattr(
        access_token_middleware,
        "decode_token_without_exp_check",
        decode_without_exp_mock,
    )

    result = await access_token_middleware.valid_access_token("expired-token")

    decode_without_exp_mock.assert_called_once_with("expired-token")
    assert result is decoded_response


@pytest.mark.asyncio
async def test_valid_access_token_returns_expired_error_when_decode_without_exp_fails(
    monkeypatch,
):
    _mock_jwks_client(monkeypatch)
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=exceptions.ExpiredSignatureError("expired")),
    )
    monkeypatch.setattr(
        access_token_middleware,
        "decode_token_without_exp_check",
        MagicMock(return_value=SimpleNamespace(ok=False)),
    )

    result = await access_token_middleware.valid_access_token("expired-token")

    assert result.sucess is False
    assert result.error.status_code == 401
    assert result.error.detail == "Token has expired"


@pytest.mark.asyncio
async def test_valid_access_token_returns_fail_response_for_invalid_audience(monkeypatch):
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
async def test_valid_access_token_returns_fail_response_for_pyjwk_client_error(monkeypatch):
    _mock_jwks_client(monkeypatch, side_effect=exceptions.PyJWKClientError("jwks down"))

    result = await access_token_middleware.valid_access_token("token")

    assert result.sucess is False
    assert result.error.status_code == 500
    assert result.error.detail == "Internal server error"


@pytest.mark.asyncio
async def test_valid_access_token_returns_fail_response_for_generic_pyjwt_error(monkeypatch):
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


def test_refresh_access_token_returns_json_on_success(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"access_token": "new-token"}
    post_mock = MagicMock(return_value=mock_response)
    monkeypatch.setattr(access_token_middleware.requests, "post", post_mock)

    result = access_token_middleware.refresh_access_token("refresh-token")

    assert result == {"access_token": "new-token"}
    post_mock.assert_called_once()


def test_refresh_access_token_raises_http_400_on_http_error(monkeypatch):
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("bad request")
    monkeypatch.setattr(
        access_token_middleware.requests, "post", MagicMock(return_value=mock_response)
    )

    with pytest.raises(HTTPException) as exc_info:
        access_token_middleware.refresh_access_token("refresh-token")

    assert exc_info.value.status_code == 400
    assert "Failed to refresh token" in exc_info.value.detail


def test_refresh_access_token_raises_http_500_on_unexpected_error(monkeypatch):
    monkeypatch.setattr(
        access_token_middleware.requests,
        "post",
        MagicMock(side_effect=RuntimeError("service unavailable")),
    )

    with pytest.raises(HTTPException) as exc_info:
        access_token_middleware.refresh_access_token("refresh-token")

    assert exc_info.value.status_code == 500
    assert "Internal server error" in exc_info.value.detail


def test_decode_token_without_exp_check_returns_ok_response(monkeypatch):
    _mock_jwks_client(monkeypatch, signing_key="decode-key")
    monkeypatch.setattr(
        access_token_middleware.jwt, "decode", MagicMock(return_value={"sub": "user-2"})
    )

    result = access_token_middleware.decode_token_without_exp_check("token")

    assert result.sucess is True
    assert result.data == {"sub": "user-2"}
    assert result.error is None


def test_decode_token_without_exp_check_returns_fail_response_on_pyjwt_error(monkeypatch):
    _mock_jwks_client(monkeypatch, signing_key="decode-key")
    monkeypatch.setattr(
        access_token_middleware.jwt,
        "decode",
        MagicMock(side_effect=jwt.PyJWTError("decode failed")),
    )

    result = access_token_middleware.decode_token_without_exp_check("token")

    assert result.sucess is False
    assert result.error.status_code == 401
    assert result.error.detail == "Invalid token: decode failed"

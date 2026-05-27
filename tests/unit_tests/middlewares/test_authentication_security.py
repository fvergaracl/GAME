from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

import app.middlewares.authentication as authentication
from app.util.check_role import check_role


@pytest.mark.asyncio
async def test_auth_api_key_or_oauth2_accepts_valid_api_key_without_oauth():
    with patch(
        "app.middlewares.authentication.auth_oauth2", new=AsyncMock()
    ) as auth_oauth2:
        result = await authentication.auth_api_key_or_oauth2(
            api_key=SimpleNamespace(data=SimpleNamespace(apiKey="k-1")),
            oauth_2_scheme="Bearer token",
        )

    assert result is True
    auth_oauth2.assert_not_awaited()


@pytest.mark.asyncio
async def test_auth_api_key_or_oauth2_falls_back_to_oauth_when_api_key_missing():
    with patch(
        "app.middlewares.authentication.auth_oauth2",
        new=AsyncMock(return_value=True),
    ) as auth_oauth2:
        result = await authentication.auth_api_key_or_oauth2(
            api_key=None,
            oauth_2_scheme="Bearer token",
        )

    assert result is True
    auth_oauth2.assert_awaited_once_with(oauth_2_scheme="Bearer token")


@pytest.mark.asyncio
async def test_auth_oauth2_rejects_missing_token():
    with patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(
                error=HTTPException(status_code=401, detail="Missing token"),
                data=None,
            )
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await authentication.auth_oauth2(oauth_2_scheme=None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_auth_oauth2_rejects_malformed_token():
    with patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(
                error=HTTPException(status_code=401, detail="Invalid token"),
                data=None,
            )
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await authentication.auth_oauth2(oauth_2_scheme="malformed-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_auth_oauth2_rejects_invalid_signature():
    with patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(
                error=HTTPException(status_code=401, detail="Invalid token signature"),
                data=None,
            )
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await authentication.auth_oauth2(oauth_2_scheme="bad-signature-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_auth_oauth2_rejects_expired_token():
    with patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(
                error=HTTPException(status_code=401, detail="Token has expired"),
                data=None,
            )
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await authentication.auth_oauth2(oauth_2_scheme="expired-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_auth_oauth2_accepts_valid_token_and_existing_user():
    with patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-1"})
        ),
    ):
        result = await authentication.auth_oauth2(oauth_2_scheme="valid-token")

    assert result is True


@pytest.mark.asyncio
async def test_auth_oauth2_accepts_valid_token_without_bootstrapping_user():
    with patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-2"})
        ),
    ):
        result = await authentication.auth_oauth2(oauth_2_scheme="valid-token")

    assert result is True


def test_check_role_security_correct_role_and_missing_role():
    token_with_role = {"realm_access": {"roles": ["AdministratorGAME", "User"]}}
    token_without_role = {"realm_access": {"roles": ["User"]}}

    assert check_role(token_with_role, "AdministratorGAME") is True
    assert check_role(token_without_role, "AdministratorGAME") is False

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import app.middlewares.authentication as authentication
from app.util.check_role import check_role


def _mock_oauth_user_service(existing_user=True):
    service = MagicMock()
    service.get_user_by_sub.return_value = (
        SimpleNamespace(id="oauth-user") if existing_user else None
    )
    service.add = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_auth_api_key_or_oauth2_accepts_valid_api_key_without_oauth():
    with patch("app.middlewares.authentication.auth_oauth2", new=AsyncMock()) as auth_oauth2:
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
    oauth_service = _mock_oauth_user_service(existing_user=True)
    with patch(
        "app.middlewares.authentication.Container.oauth_users_service",
        return_value=oauth_service,
    ), patch(
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
    oauth_service = _mock_oauth_user_service(existing_user=True)
    with patch(
        "app.middlewares.authentication.Container.oauth_users_service",
        return_value=oauth_service,
    ), patch(
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
    oauth_service = _mock_oauth_user_service(existing_user=True)
    with patch(
        "app.middlewares.authentication.Container.oauth_users_service",
        return_value=oauth_service,
    ), patch(
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
async def test_auth_oauth2_accepts_expired_token_via_decode_without_expiration_check():
    oauth_service = _mock_oauth_user_service(existing_user=False)
    with patch(
        "app.middlewares.authentication.Container.oauth_users_service",
        return_value=oauth_service,
    ), patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(
                error=HTTPException(status_code=401, detail="Token has expired"),
                data=None,
            )
        ),
    ), patch(
        "app.middlewares.authentication.decode_token_without_exp_check",
        return_value=SimpleNamespace(data={"sub": "oauth-user-1"}),
    ):
        result = await authentication.auth_oauth2(oauth_2_scheme="expired-token")

    assert result is True
    oauth_service.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_auth_oauth2_expired_token_fallback_failure_still_returns_401():
    oauth_service = _mock_oauth_user_service(existing_user=True)
    with patch(
        "app.middlewares.authentication.Container.oauth_users_service",
        return_value=oauth_service,
    ), patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(
                error=HTTPException(status_code=401, detail="Token has expired"),
                data=None,
            )
        ),
    ), patch(
        "app.middlewares.authentication.decode_token_without_exp_check",
        side_effect=RuntimeError("decode failed"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await authentication.auth_oauth2(oauth_2_scheme="expired-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.asyncio
async def test_auth_oauth2_accepts_valid_token_and_existing_user():
    oauth_service = _mock_oauth_user_service(existing_user=True)
    with patch(
        "app.middlewares.authentication.Container.oauth_users_service",
        return_value=oauth_service,
    ), patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-1"})
        ),
    ):
        result = await authentication.auth_oauth2(oauth_2_scheme="valid-token")

    assert result is True
    oauth_service.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_auth_oauth2_accepts_valid_token_and_creates_missing_user():
    oauth_service = _mock_oauth_user_service(existing_user=False)
    with patch(
        "app.middlewares.authentication.Container.oauth_users_service",
        return_value=oauth_service,
    ), patch(
        "app.middlewares.authentication.valid_access_token",
        new=AsyncMock(
            return_value=SimpleNamespace(error=None, data={"sub": "oauth-user-2"})
        ),
    ):
        result = await authentication.auth_oauth2(oauth_2_scheme="valid-token")

    assert result is True
    oauth_service.add.assert_awaited_once()


def test_check_role_security_correct_role_and_missing_role():
    token_with_role = {"realm_access": {"roles": ["AdministratorGAME", "User"]}}
    token_without_role = {"realm_access": {"roles": ["User"]}}

    assert check_role(token_with_role, "AdministratorGAME") is True
    assert check_role(token_without_role, "AdministratorGAME") is False

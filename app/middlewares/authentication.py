from fastapi import Depends, HTTPException, status

from app.core.container import Container
from app.middlewares.valid_access_token import (
    oauth_2_scheme, valid_access_token, decode_token_without_exp_check
)
from app.schema.oauth_users_schema import CreateOAuthUser
from app.services.apikey_service import ApiKeyService


async def auth_api_key_or_oauth2(
    api_key: str = Depends(ApiKeyService.get_api_key_header),
    # token is "Authorization: Bearer " got from the header
    oauth_2_scheme: str = Depends(oauth_2_scheme),
):
    """
    Authenticate using API Key or OAuth2.

    This function first attempts to authenticate the request using an API key.
      If the API key is valid and present, it returns `True`. If the API key
        authentication fails or no API key is provided, it falls back to
          OAuth2 authentication using the provided OAuth2 token scheme.

    Args:
        api_key (str): The API key provided via the `Authorization` header.
          Retrieved via `ApiKeyService.get_api_key_header`.
        oauth_2_scheme (str): The OAuth2 token extracted from the
          `Authorization` header, with the "Bearer" scheme. Retrieved via
            `oauth_2_scheme`.

    Returns:
        bool: Returns `True` if either the API key or OAuth2 token is valid.
          If both authentication mechanisms fail, an HTTP 401 exception is
            raised.
    """

    if api_key and api_key.data:

        return True
    return await auth_oauth2(oauth_2_scheme=oauth_2_scheme)


async def auth_oauth2(
    oauth_2_scheme: str = Depends(oauth_2_scheme),
):
    """
    Authenticate using OAuth2 token.

    This function attempts to authenticate the request using an OAuth2 token.

    Args:
        oauth_2_scheme (str): The OAuth2 token extracted from the
          `Authorization` header, with the "Bearer" scheme.
            Retrieved via `oauth_2_scheme`.

    Returns:
        bool: Returns `True` if the OAuth2 token is valid. Raises an HTTP 401
          exception if token validation fails.

    Raises:
        HTTPException: Raises a 401 Unauthorized error if OAuth2
          authentication fails.
    """

    oauth_user_service = Container.oauth_users_service()
    try:
        is_valid = await valid_access_token(oauth_2_scheme)
        if is_valid.error:
            raise is_valid.error
        user = oauth_user_service.get_user_by_sub(is_valid.data["sub"])
        if not user:
            create_user = CreateOAuthUser(
                provider="keycloak",
                provider_user_id=is_valid.data["sub"],
                status="active",
            )
            await oauth_user_service.add(create_user)
        return True
    except HTTPException as e:

        if e.status_code == 401 and "Token has expired" in str(e.detail):
            try:
                decoded_token = decode_token_without_exp_check(oauth_2_scheme)
                user = oauth_user_service.get_user_by_sub(
                    decoded_token.data["sub"])
                if not user:
                    create_user = CreateOAuthUser(
                        provider="keycloak",
                        provider_user_id=decoded_token.data["sub"],
                        status="active",
                    )
                    await oauth_user_service.add(create_user)
                return True
            except Exception as inner_error:
                print("Validation without expiration check failed")
                print(inner_error)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

from fastapi import Depends, HTTPException, status

from app.middlewares.valid_access_token import oauth_2_scheme, valid_access_token
from app.services.apikey_service import ApiKeyService


async def auth_api_key_or_oauth2(
    api_key: str = Depends(ApiKeyService.get_api_key_header),
    # token is "Authorization: Bearer " got from the header
    oauth_2_scheme: str = Depends(oauth_2_scheme),
):
    """Authenticate a request using an API key or, failing that, OAuth2.

    The API key is tried first: if a valid key is present the request is
    authenticated immediately. Otherwise the request falls back to OAuth2
    bearer-token validation.

    Args:
        api_key (str): The API key resolved from the ``X-API-Key`` header
            via ``ApiKeyService.get_api_key_header``.
        oauth_2_scheme (str): The OAuth2 bearer token extracted from the
            ``Authorization`` header.

    Returns:
        bool: ``True`` if either credential is valid.

    Raises:
        HTTPException: ``401`` if both mechanisms fail.
    """

    if api_key and api_key.data:

        return True
    return await auth_oauth2(oauth_2_scheme=oauth_2_scheme)


async def auth_oauth2(
    oauth_2_scheme: str = Depends(oauth_2_scheme),
):
    """Authenticate a request using an OAuth2 bearer token.

    Args:
        oauth_2_scheme (str): The OAuth2 bearer token extracted from the
            ``Authorization`` header.

    Returns:
        bool: ``True`` if the token is valid.

    Raises:
        HTTPException: ``401`` if OAuth2 authentication fails.
    """

    try:
        is_valid = await valid_access_token(oauth_2_scheme)
        if is_valid.error:
            raise is_valid.error
        return True
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

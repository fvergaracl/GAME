import asyncio
import logging
from typing import Annotated, Any, Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jwt import PyJWKClient, exceptions

from app.core.config import configs
from app.util.response import Response

logger = logging.getLogger(__name__)


OIDC_SCOPES = {
    "openid": "OpenID Connect scope required for subject claims.",
    "profile": "Basic profile claims.",
    "email": "Email claims.",
    "greencrowd-roles": "GreenCrowd role claims.",
}

SUBJECT_FALLBACK_CLAIMS = (
    "sub",
    "preferred_username",
    "email",
    "client_id",
    "azp",
)


# Lazy module-level singleton. Building a fresh PyJWKClient per request issues
# a JWKS HTTP roundtrip every time; reusing one client lets it cache signing
# keys for ``lifespan`` seconds.
_JWKS_CLIENT: Optional[PyJWKClient] = None


def _get_jwks_client() -> PyJWKClient:
    global _JWKS_CLIENT
    if _JWKS_CLIENT is None:
        url = f"{configs.KEYCLOAK_URL_DOCKER}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/certs"
        _JWKS_CLIENT = PyJWKClient(
            url,
            headers={"User-agent": "fastapi-jwt-auth/0.1.0 ( GAME )"},
            cache_keys=True,
            lifespan=300,
        )
    return _JWKS_CLIENT


def _reset_jwks_client_for_tests() -> None:
    """Test hook: drop the cached PyJWKClient so monkeypatched classes apply."""
    global _JWKS_CLIENT
    _JWKS_CLIENT = None


class CustomOAuth2AuthorizationCodeBearer(OAuth2AuthorizationCodeBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        try:
            token = await super().__call__(request)
        except HTTPException:
            return False
        return token


oauth_2_scheme = CustomOAuth2AuthorizationCodeBearer(
    tokenUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",
    authorizationUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/auth",
    refreshUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",
    scopes=OIDC_SCOPES,
)


def _normalize_subject_claim(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    for claim_name in SUBJECT_FALLBACK_CLAIMS:
        claim_value = normalized.get(claim_name)
        if isinstance(claim_value, str) and claim_value.strip():
            normalized["sub"] = claim_value.strip()
            break
    return normalized


def _build_token_response(payload: dict[str, Any]) -> Response:
    normalized = _normalize_subject_claim(payload)
    subject = normalized.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        return Response.fail(
            error=HTTPException(
                status_code=401, detail="Token subject not found")
        )
    return Response.ok(normalized)


async def valid_access_token(
    access_token: Annotated[str, Depends(oauth_2_scheme)]
) -> Response:
    try:
        jwks_client = _get_jwks_client()
        # PyJWKClient does sync HTTP under the hood; offload to a worker thread
        # so a JWKS roundtrip doesn't stall the event loop.
        signing_key = await asyncio.to_thread(
            jwks_client.get_signing_key_from_jwt, access_token
        )
        data = jwt.decode(
            access_token,
            key=signing_key.key,
            algorithms=["RS256"],
            issuer=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}",
            audience=configs.KEYCLOAK_AUDIENCE,
            leeway=30,
            options={
                "verify_exp": True,
                "verify_aud": True,
            },
        )
        return _build_token_response(data)

    except exceptions.InvalidSignatureError as e:
        logger.warning("JWT rejected: invalid signature: %s", e)
        return Response.fail(
            error=HTTPException(
                status_code=401, detail="Invalid token signature")
        )

    except exceptions.ExpiredSignatureError as e:
        logger.warning("JWT rejected: expired: %s", e)
        return Response.fail(
            error=HTTPException(status_code=401, detail="Token has expired")
        )
    except exceptions.InvalidAudienceError as e:
        logger.warning("JWT rejected: invalid audience: %s", e)
        return Response.fail(
            error=HTTPException(status_code=403, detail="Invalid audience")
        )
    except exceptions.InvalidTokenError as e:
        logger.warning("JWT rejected: invalid token: %s", e)
        return Response.fail(
            error=HTTPException(status_code=401, detail="Invalid token")
        )
    except exceptions.PyJWKClientError:
        logger.exception("JWKS client failure fetching signing key")
        return Response.fail(
            error=HTTPException(
                status_code=500, detail="Internal server error")
        )
    except jwt.PyJWTError as e:
        logger.warning("JWT rejected: %s", e)
        return Response.fail(
            error=HTTPException(
                status_code=401, detail=f"Invalid token: {str(e)}")
        )


async def refresh_access_token(refresh_token: str):
    """
    Refresh the access token using the refresh token.

    Args:
        refresh_token (str): The refresh token to be used to generate a new
          access token.

    Returns:
        dict: The new access token and other related information.
    """
    url = f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": configs.KEYCLOAK_CLIENT_ID,
        "client_secret": configs.KEYCLOAK_CLIENT_SECRET,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as http_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh token: {http_err}",
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {err}",
        )

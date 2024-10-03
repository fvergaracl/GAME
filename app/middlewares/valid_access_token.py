from typing import Annotated, Optional
import jwt
import requests
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from jwt import PyJWKClient, exceptions
from app.util.response import Response
from app.core.config import configs


class CustomOAuth2AuthorizationCodeBearer(OAuth2AuthorizationCodeBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        try:
            token = await super().__call__(request)
        except HTTPException as e:
            token = None
            return False
        return token


oauth_2_scheme = CustomOAuth2AuthorizationCodeBearer(
    tokenUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",
    authorizationUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/auth",
    refreshUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",
)


async def valid_access_token(
    access_token: Annotated[str, Depends(oauth_2_scheme)]
) -> Response:
    url = f"{configs.KEYCLOAK_URL_DOCKER}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    optional_custom_headers = {"User-agent": "fastapi-jwt-auth/0.1.0 ( GAME )"}
    jwks_client = PyJWKClient(url, headers=optional_custom_headers)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(access_token)
        data = jwt.decode(
            access_token,
            key=signing_key.key,
            algorithms=["RS256"],
            issuer=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}",
            audience=configs.KEYCLOAK_AUDIENCE,
            options={"verify_exp": True},
        )
        return Response.ok(data)

    except exceptions.InvalidSignatureError as e:
        print(f"Error: InvalidSignatureError - {e}")
        return Response.fail(
            error=HTTPException(
                status_code=401,
                detail="Invalid token signature"
            )
        )

    except exceptions.ExpiredSignatureError as e:
        print(f"Error: ExpiredSignatureError - {e}")
        return Response.fail(
            error=HTTPException(
                status_code=401,
                detail="Token has expired"
            )
        )
    except exceptions.InvalidAudienceError as e:
        print(f"Error: InvalidAudienceError - {e}")
        return Response.fail(
            error=HTTPException(
                status_code=403,
                detail="Invalid audience"
            )
        )
    except exceptions.InvalidTokenError as e:
        print(f"Error: InvalidTokenError - {e}")
        return Response.fail(
            error=HTTPException(
                status_code=401,
                detail="Invalid token"
            )
        )
    except exceptions.PyJWKClientError as e:
        print(f"Error: PyJWKClientError - {e}")
        return Response.fail(
            error=HTTPException(
                status_code=500,
                detail="Internal server error"
            )
        )


def refresh_access_token(refresh_token: str):
    """
    Refresh the access token using the refresh token.

    Args:
        refresh_token (str): The refresh token to be used to generate a new access token.

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
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as http_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh token: {http_err}"
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {err}"
        )

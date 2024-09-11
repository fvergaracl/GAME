from typing import Annotated

import jwt
import requests
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from jwt import PyJWKClient, exceptions

from app.core.config import configs

oauth_2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",  # noqa
    authorizationUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/auth",  # noqa
    refreshUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",  # noqa
)


async def valid_access_token(access_token: Annotated[str, Depends(oauth_2_scheme)]):
    url = f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/certs"  # noqa
    optional_custom_headers = {"User-agent": "custom-user-agent"}

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
        return data

    except exceptions.InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid token signature")
    except exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except exceptions.InvalidAudienceError:
        raise HTTPException(status_code=403, detail="Invalid audience")
    except exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Not authenticated")
    except exceptions.PyJWKClientError:
        raise HTTPException(status_code=500, detail="Internal server error")


def refresh_access_token(refresh_token: Annotated[str, Depends(oauth_2_scheme)]):
    """
    Refresh the access token using the refresh token.
    """

    url = f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token"  # noqa
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": configs.KEYCLOAK_CLIENT_ID,
        "client_secret": configs.KEYCLOAK_CLIENT_SECRET,
    }

    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()

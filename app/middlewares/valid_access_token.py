import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from app.core.config import configs
from typing import Annotated
from jwt import PyJWKClient, exceptions

# OAuth2 scheme configuration with Keycloak URLs
oauth_2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",
    authorizationUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/auth",
    refreshUrl=f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token"
)


async def valid_access_token(
    access_token: Annotated[str, Depends(oauth_2_scheme)]
):
    url = f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    optional_custom_headers = {"User-agent": "custom-user-agent"}

    jwks_client = PyJWKClient(url, headers=optional_custom_headers)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(access_token)

        data = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=configs.KEYCLOAK_CLIENT_ID,
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

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from app.core.config import configs
from typing import Annotated

oauth_2_scheme = OAuth2AuthorizationCodeBearer(
    tokenUrl=f"{configs.KEYCLOAK_URL}/admin/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token",
    authorizationUrl=f"{configs.KEYCLOAK_URL}/admin/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/auth",
    refreshUrl=f"{configs.KEYCLOAK_URL}/admin/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/token"
    # tokenUrl="http://path/to/realm/protocol/openid-connect/token",
    # authorizationUrl="http://path/to/realm/protocol/openid-connect/auth",
    # refreshUrl="http://path/to/realm/protocol/openid-connect/token",
)


async def valid_access_token(
    access_token: Annotated[str, Depends(oauth_2_scheme)]
):
    # url = "http://keycloak:8080/realms/tuto/protocol/openid-connect/certs"
    url = f"{configs.KEYCLOAK_URL}/realms/{configs.KEYCLOAK_REALM}/protocol/openid-connect/certs"
    optional_custom_headers = {"User-agent": "custom-user-agent"}
    jwks_client = jwt.PyJWKClient(url, headers=optional_custom_headers)

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(access_token)
        data = jwt.decode(
            access_token,
            signing_key.key,
            algorithms=["RS256"],
            audience="api",
            options={"verify_exp": True},
        )
        return data
    except jwt.exceptions.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Not authenticated")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schema.apikey_schema import ApiKeyCreated
from unittest.mock import AsyncMock, patch
from app.core.exceptions import HTTPException
from freezegun import freeze_time

client = TestClient(app)

valid_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJaX0tTOGNvZUJSNHVNTUIyVUsxMDlKWEI3UXF4N3dyRkNSdEFEaTFUYUpNIn0.eyJleHAiOjE3MjY2ODM2NTEsImlhdCI6MTcyNjY0NzY1MiwiYXV0aF90aW1lIjoxNzI2NjQ3NjUxLCJqdGkiOiI1MDdiMmM4Yi1jNWRhLTRmMGMtYmUwZS04ZDI3MWI4N2JiMzIiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvcmVhbG1zL2dhbWVSZWFsbSIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiJhYjI1Y2M5NC0yZGQ1LTQ5OTYtYjUxNy1lYjRiMTUyMzI4NzYiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJnYW1lQVBJIiwic2lkIjoiNzc5ODlkODMtN2E1ZC00MGI3LTk1NjYtNDQ5YTEzOWQ2ZjZjIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIiLCIqIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLWdhbWVyZWFsbSIsIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwiQWRtaW5pc3RyYXRvckdBTUUiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoiZW1haWwgcHJvZmlsZSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6ImZlbGlwZSB2ZXJnYXJhIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZmVsaXBlLnZlcmdhcmFAZGV1c3RvLmVzIiwiZ2l2ZW5fbmFtZSI6ImZlbGlwZSIsImZhbWlseV9uYW1lIjoidmVyZ2FyYSIsImVtYWlsIjoiZmVsaXBlLnZlcmdhcmFAZGV1c3RvLmVzIn0.Uk5patlWI5p9frpccH5XYTb3q9otZ5i6pAanEEFRukQRQ6I3Gx7Xs-pqzSFfDJ3FGmv9TpASkP9BPW33yvG5UhQvW7fYsWtl2RELor_Dzdja1P8X20L4wtKlltzFZV4e9XvvPRkTQ52-FgsPWnujYR9pKYH_NiQx0QKyLzgA8me0wogUuhPiZTlYSORuUhnbdQedYMcogPZJpRy9JWjmsT4_1NyksPIAoxhvBRkEabe2vkKOOeCVSmYGML9o34zfh33X5q9o8vyFV3eVcOMLJxJ7Xi1PuMgF98_xn7DvtyMndwRX769FkVh4cGQenwYvqiZoAkEOQb5HtcpYbfDHbA"  # noqa
unauthorized_valid_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJaX0tTOGNvZUJSNHVNTUIyVUsxMDlKWEI3UXF4N3dyRkNSdEFEaTFUYUpNIn0.eyJleHAiOjE3MjY2ODY1MjksImlhdCI6MTcyNjY1MDUyOSwiYXV0aF90aW1lIjoxNzI2NjUwNTI5LCJqdGkiOiJkOWYxMTRiNi1hYTk5LTQwMTQtODNkYi02ZDBjMTc0ZTEyNTYiLCJpc3MiOiJodHRwOi8vbG9jYWxob3N0OjgwODAvcmVhbG1zL2dhbWVSZWFsbSIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiIwZDQyYTFhNy0xM2VhLTRiOTMtOWVlNC0wOTliOWQxZjM5YWIiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJnYW1lQVBJIiwic2lkIjoiZDVmNjAxYzEtMGM5OS00YWNjLTkzMmYtN2RkZmIyMmM2ODBhIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyIiLCIqIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLWdhbWVyZWFsbSIsIm9mZmxpbmVfYWNjZXNzIiwidW1hX2F1dGhvcml6YXRpb24iXX0sInJlc291cmNlX2FjY2VzcyI6eyJhY2NvdW50Ijp7InJvbGVzIjpbIm1hbmFnZS1hY2NvdW50IiwibWFuYWdlLWFjY291bnQtbGlua3MiLCJ2aWV3LXByb2ZpbGUiXX19LCJzY29wZSI6ImVtYWlsIHByb2ZpbGUiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJGZWxpcGUgVmVyZ2FyYSBCb3JnZSIsInByZWZlcnJlZF91c2VybmFtZSI6ImZlbGlwZS52ZXJnYXJhK25vYWRtaW5AZGV1c3RvLmVzIiwiZ2l2ZW5fbmFtZSI6IkZlbGlwZSIsImZhbWlseV9uYW1lIjoiVmVyZ2FyYSBCb3JnZSIsImVtYWlsIjoiZmVsaXBlLnZlcmdhcmErbm9hZG1pbkBkZXVzdG8uZXMifQ.Os7oRfTHS-EYZnZR7h2Zti0htbn8ua2MsObO1vWNkIpFrXahg9UVNOoBKsuBCHULowkM1DsU6r_goJfRNNb1rZP9aRFOd9i6WLEX74me27bGSZDeYGJkzwIC1rLLpDBLlr5R0HNo7pNvR9YlYC5jj9axMPvZOBUOr8p55UUGus3O91x_vhbsYO-nUukAsshPMnrgLA8gK8zPb2Df3XtOv7KNFHaQOi9lGdnbdPuV93xyEUn1httuOW9vOUxtojlbCXRV_ocT3fDSrBTtB24d62MqEkj_BflbJj9ldwiIE4Yjv7ylnwEURo04K3Kw_8PXWPkgkYNg8zraw4LAzJvgsQ"  # noqa

mock_decoded_token = {
    "data": {"sub": "test_user", "roles": ["AdministratorGAME"]},
    "error": None,
}
mock_api_key_response = ApiKeyCreated(
    id="test_id",
    apiKey="test_api_key",
    createdBy="test_user",
    client="test_client",
    description="Test API Key Description",
    message="API Key created successfully",
)


def serialize_exception(exc: HTTPException) -> dict:
    print("-----------------")
    print("-----------------")
    print("-----------------")
    print("-----------------")
    print("-----------------")
    print("-----------------")
    print("-----------------")
    print({"status_code": exc.status_code, "detail": exc.detail})
    print("******************")
    print("******************")
    print("******************")
    print("******************")
    print("******************")
    return {"status_code": exc.status_code, "detail": exc.detail}


@pytest.fixture
def mock_valid_token():
    with patch(
        "app.middlewares.authentication.oauth_2_scheme", return_value=valid_token
    ) as mock:
        yield mock


@pytest.fixture
def mock_valid_access_token():
    token_data = {"sub": "test_user", "roles": ["AdministratorGAME"]}
    with patch(
        "app.middlewares.valid_access_token.valid_access_token", return_value=token_data
    ) as mock:
        yield mock


@pytest.fixture
def mock_unauthorized_valid_token():
    with patch(
        "app.middlewares.authentication.oauth_2_scheme",
        return_value=unauthorized_valid_token,
    ) as mock:
        yield mock


@pytest.fixture
def mock_api_key_service():
    with patch("app.services.apikey_service.ApiKeyService") as mock:
        service = mock.return_value
        service.generate_api_key_service = AsyncMock(return_value="test_api_key")
        service.create_api_key = AsyncMock(return_value=mock_api_key_response)
        service.get_all_api_keys = AsyncMock(return_value=[mock_api_key_response])
        yield service


@pytest.mark.asyncio
@freeze_time("2024-09-18 11:00:00")
async def test_get_all_api_keys_success(
    mock_valid_access_token, mock_api_key_service, mock_valid_token
):
    response = client.get(
        "/api/v1/apikey/", headers={"Authorization": f"Bearer {valid_token}"}
    )

    assert response.status_code == 200

    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) > 0
    assert "apiKey" in response_json[0]
    assert "client" in response_json[0]
    assert "description" in response_json[0]


@pytest.mark.asyncio
@freeze_time("2024-09-18 11:00:00")
async def test_create_api_key_success(
    mock_valid_access_token, mock_api_key_service, mock_valid_token
):
    payload = {"client": "Test API Key", "description": "Test description"}

    response = client.post(
        "/api/v1/apikey/create",
        json=payload,
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    print("1111111111111111111111111111111")
    print("1111111111111111111111111111111")
    print("1111111111111111111111111111111")
    print("1111111111111111111111111111111")
    print("1111111111111111111111111111111")
    print(response.status_code)
    print(response.json())
    assert response.status_code == 201

    response_json = response.json()
    assert "apiKey" in response_json
    assert response_json["client"] == payload["client"]
    assert response_json["description"] == payload["description"]
    assert response_json["message"] == "API Key created successfully"


@pytest.mark.asyncio
@freeze_time("2024-09-19 10:00:00")  # Dentro del tiempo de vida del token
async def test_create_api_key_forbidden(
    mock_valid_access_token, mock_api_key_service, mock_unauthorized_valid_token
):
    """
    Test that a user without the AdministratorGAME role cannot create an API
    key.
    """
    # Este token simula la falta del rol "AdministratorGAME"
    mock_invalid_token = {
        "data": {"sub": "test_user", "roles": ["User"]},
        "error": None,
    }

    # Simulación de la validación del token sin el rol adecuado
    with patch(
        "app.middlewares.valid_access_token.valid_access_token",
        return_value=mock_invalid_token,
    ):
        payload = {"client": "Test API Key", "description": "Test description"}

        response = client.post(
            "/api/v1/apikey/create",
            json=payload,
            headers={"Authorization": f"Bearer {unauthorized_valid_token}"},
        )

        print("---------")
        print("-----------------------------------222222222222")
        print(response.status_code)
        print(response.json())
        print("-***************")

        # Cambia el código de estado esperado a 403 Forbidden
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "You do not have permission to create an API key"
        )


@pytest.mark.asyncio
async def test_get_all_api_keys_forbidden(mock_api_key_service):
    mock_invalid_token = {
        "data": {"sub": "test_user", "roles": ["User"]},
        "error": None,
    }

    with patch(
        "app.middlewares.valid_access_token.valid_access_token",
        return_value=mock_invalid_token,
    ):
        response = client.get(
            "/api/v1/apikey",
            headers={"Authorization": f"Bearer {unauthorized_valid_token}"},
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Token has expired"


@pytest.mark.asyncio
async def test_create_api_key_invalid_token(mock_api_key_service):
    invalid_token_response = {
        "error": serialize_exception(
            HTTPException(status_code=401, detail="Invalid token signature")
        )
    }
    print("-> 1")
    with patch(
        "app.middlewares.valid_access_token.valid_access_token",
        return_value=invalid_token_response,
    ):
        print("-> 2")
        payload = {"client": "Test API Key", "description": "Test description"}
        print("-> 3")
        response = client.post(
            "/api/v1/apikey/create",
            json=payload,
            headers={"Authorization": "Bearer invalid_token"},
        )
        print("-> 4")
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_get_all_api_keys_invalid_token(mock_api_key_service):

    invalid_token_response = {
        "error": serialize_exception(
            HTTPException(status_code=401, detail="Invalid token signature")
        )
    }

    with patch(
        "app.middlewares.valid_access_token.valid_access_token",
        return_value=invalid_token_response,
    ):
        response = client.get(
            "/api/v1/apikey/", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
@freeze_time("2100-01-01")
async def test_get_all_api_keys_token_expired(mock_api_key_service):

    invalid_token_response = {
        "error": serialize_exception(
            HTTPException(status_code=401, detail="Invalid token signature")
        )
    }

    with patch(
        "app.middlewares.valid_access_token.valid_access_token",
        return_value=invalid_token_response,
    ):
        response = client.get(
            "/api/v1/apikey/", headers={"Authorization": "Bearer" + valid_token}
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"

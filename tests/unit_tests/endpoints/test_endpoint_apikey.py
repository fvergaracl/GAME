import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app
from app.api.v1.endpoints.apikey import create_api_key


BASE_URL = os.getenv("TEST_API_URL_DOCKER", "http://localhost:8000")


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    mock_service = AsyncMock()
    mock_service.generate_api_key_service.return_value = "mocked-api-key"
    mock_service.create_api_key.return_value.dict.return_value = {
        "client": "test-client",
        "description": "desc",
        "apiKey": "mocked-api-key",
        "createdBy": "user123"
    }

    mock_logs_service = AsyncMock()
    mock_oauth_service = AsyncMock()
    mock_oauth_service.get_user_by_sub.return_value = None
    mock_oauth_service.add = AsyncMock()

    mock_token = AsyncMock()
    mock_token.data = {"sub": "user123"}
    mock_token.error = None

    monkeypatch.setattr("app.api.v1.endpoints.apikey.valid_access_token", AsyncMock(
        return_value=mock_token))
    monkeypatch.setattr(
        "app.api.v1.endpoints.apikey.check_role", lambda token, role: True)
    monkeypatch.setattr("app.api.v1.endpoints.apikey.add_log", AsyncMock())

    app.dependency_overrides = {
        "app.api.v1.endpoints.apikey.oauth_2_scheme": lambda: "Bearer mocked_token",
        "app.api.v1.endpoints.apikey.ApiKeyService": lambda: mock_service,
        "app.api.v1.endpoints.apikey.LogsService": lambda: mock_logs_service,
        "app.api.v1.endpoints.apikey.OAuthUsersService": lambda: mock_oauth_service,
    }

    yield

    app.dependency_overrides = {}  # Limpieza después de cada test


def test_create_api_key_success(test_client):
    payload = {
        "client": "test-client",
        "description": "desc"
    }

    response = test_client.post(
        f"{BASE_URL}/apikey/create", json=payload,
        headers={"Authorization": "Bearer mocked_token"})

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "API Key created successfully"
    assert data["apiKey"] == "mocked-api-key"

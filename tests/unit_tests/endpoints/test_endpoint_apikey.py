from unittest.mock import AsyncMock

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient

from app.main import app, container  # ✅ usa container real (instancia)


@pytest.fixture
def test_client():
    return TestClient(app)


class FakeResponse:
    def dict(self):
        return {
            "client": "test-client",
            "description": "desc",
            "apiKey": "mocked-api-key",
            "createdBy": "user123",
        }


@pytest.fixture(autouse=True)
def override_di(monkeypatch):
    # --- mocks ---
    mock_service = AsyncMock()
    mock_service.generate_api_key_service.return_value = "mocked-api-key"
    mock_service.create_api_key = AsyncMock(return_value=FakeResponse())

    mock_logs_service = AsyncMock()

    mock_oauth_service = AsyncMock()
    mock_oauth_service.get_user_by_sub.return_value = None
    mock_oauth_service.add = AsyncMock()

    mock_token = AsyncMock()
    mock_token.data = {"sub": "user123"}
    mock_token.error = None

    # --- patch helpers inside endpoint module ---
    monkeypatch.setattr(
        "app.api.v1.endpoints.apikey.valid_access_token",
        AsyncMock(return_value=mock_token),
    )
    monkeypatch.setattr(
        "app.api.v1.endpoints.apikey.check_role", lambda token, role: True
    )
    monkeypatch.setattr("app.api.v1.endpoints.apikey.add_log", AsyncMock())

    # ✅ override providers on the *real container instance*
    container.apikey_service.override(providers.Object(mock_service))
    container.logs_service.override(providers.Object(mock_logs_service))
    container.oauth_users_service.override(providers.Object(mock_oauth_service))

    yield

    container.apikey_service.reset_override()
    container.logs_service.reset_override()
    container.oauth_users_service.reset_override()


def test_create_api_key_success(test_client):
    payload = {"client": "test-client", "description": "desc"}

    response = test_client.post(
        "/api/v1/apikey/create",
        json=payload,
        headers={"Authorization": "Bearer mocked_token"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "API Key created successfully"
    assert data["apiKey"] == "mocked-api-key"

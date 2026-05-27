from unittest.mock import AsyncMock

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient

from app.main import app, container  # ✅ usa container real (instancia)
from app.middlewares.authentication import auth_oauth2
from app.util.generate_api_key import GeneratedApiKey


@pytest.fixture
def test_client():
    return TestClient(app)


class FakeResponse:
    def model_dump(self):
        return {
            "client": "test-client",
            "description": "desc",
            "apiKey": "gme_live_mockedp",
            "apiKeyHash": "deadbeef",
            "createdBy": "user123",
        }


MOCK_GENERATED = GeneratedApiKey(
    plaintext="gme_live_mockedp.payload-payload-payload-payload-pad",
    prefix="gme_live_mockedp",
    key_hash="deadbeef",
)


@pytest.fixture(autouse=True)
def override_di(monkeypatch):
    # --- mocks ---
    mock_service = AsyncMock()
    mock_service.generate_api_key_service.return_value = MOCK_GENERATED
    mock_service.create_api_key = AsyncMock(return_value=FakeResponse())

    mock_logs_service = AsyncMock()

    mock_oauth_service = AsyncMock()
    mock_oauth_service.get_user_by_sub.return_value = None
    mock_oauth_service.add = AsyncMock()

    mock_token = AsyncMock()
    mock_token.data = {"sub": "user123"}
    mock_token.error = None

    # --- patch helpers used by auth dependencies ---
    monkeypatch.setattr(
        "app.middlewares.authentication.valid_access_token",
        AsyncMock(return_value=mock_token),
    )
    monkeypatch.setattr(
        "app.middlewares.auth_context.valid_access_token",
        AsyncMock(return_value=mock_token),
    )
    monkeypatch.setattr(
        "app.middlewares.auth_context.check_role", lambda token, role: True
    )
    monkeypatch.setattr("app.middlewares.auth_context.add_log", AsyncMock())

    # ✅ override providers on the *real container instance*
    container.apikey_service.override(providers.Object(mock_service))
    container.logs_service.override(providers.Object(mock_logs_service))
    container.oauth_users_service.override(providers.Object(mock_oauth_service))

    async def _auth_override():
        return True

    app.dependency_overrides[auth_oauth2] = _auth_override

    yield

    app.dependency_overrides.pop(auth_oauth2, None)
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
    # The public prefix is stable and returned on every read.
    assert data["apiKey"] == "gme_live_mockedp"
    # The plaintext is included exactly once at creation.
    assert data["plaintext"] == MOCK_GENERATED.plaintext

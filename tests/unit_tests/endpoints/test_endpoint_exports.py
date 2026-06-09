import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient

from app.main import app, container


@pytest.fixture
def test_client():
    return TestClient(app)


async def _aiter(items):
    for it in items:
        yield it


def _make_mock_service(rows):
    """
    Build a mock ExportService whose iter_dataset returns the given rows.

    We can't reuse `ExportService.format_iterator` directly because it
    dispatches through ``self.format_as_csv`` etc., and ``self`` is an
    AsyncMock - every attribute access yields an AsyncMock that returns a
    coroutine, breaking ``async for``. So we route to the underlying
    staticmethods explicitly.
    """
    from app.services.export_service import DATASET_COLUMNS, ExportService

    service = AsyncMock()
    service.audit_start = AsyncMock(return_value=SimpleNamespace(id="audit-1"))
    service.audit_finish = AsyncMock()
    service.iter_dataset = lambda dataset_type, filters: _aiter(rows)

    def _format_iterator(dt, fmt, it):
        if fmt == "csv":
            return ExportService.format_as_csv(it, DATASET_COLUMNS[dt])
        if fmt == "json":
            return ExportService.format_as_json(it)
        return ExportService.format_as_xlsx(it, DATASET_COLUMNS[dt])

    service.format_iterator = _format_iterator
    service.media_type_for = ExportService.media_type_for
    service.filename_for = ExportService.filename_for
    return service


def _patch_admin_auth(monkeypatch, *, is_admin: bool):
    """
    Stub out the OIDC pipeline so get_auth_context resolves to an admin
    (or non-admin) without touching Keycloak.
    """
    mock_token = SimpleNamespace(
        data={"sub": "admin-user", "realm_access": {"roles": []}},
        error=None,
    )
    monkeypatch.setattr(
        "app.middlewares.auth_context.valid_access_token",
        AsyncMock(return_value=mock_token),
    )
    monkeypatch.setattr(
        "app.middlewares.auth_context.check_role",
        lambda token, role: is_admin,
    )
    monkeypatch.setattr("app.middlewares.auth_context.add_log", AsyncMock())


@pytest.fixture(autouse=True)
def override_di_logs(monkeypatch):
    mock_logs_service = AsyncMock()
    mock_oauth_service = AsyncMock()
    mock_oauth_service.get_user_by_sub.return_value = SimpleNamespace(
        provider_user_id="admin-user"
    )

    container.logs_service.override(providers.Object(mock_logs_service))
    container.oauth_users_service.override(providers.Object(mock_oauth_service))
    yield
    container.logs_service.reset_override()
    container.oauth_users_service.reset_override()


def test_export_users_csv_returns_streamed_csv(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=True)
    rows = [
        {
            "id": "u1",
            "externalUserId": "ext-1",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-02T00:00:00",
            "apiKey_used": "gme_live_a",
            "oauth_user_id": None,
        }
    ]
    mock_service = _make_mock_service(rows)
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/users?format=csv&limit=10",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    body = response.content.decode("utf-8")
    header_line = body.splitlines()[0]
    assert "externalUserId" in header_line
    assert "ext-1" in body

    mock_service.audit_start.assert_awaited_once()
    mock_service.audit_finish.assert_awaited_once()
    assert mock_service.audit_finish.await_args.kwargs["status"] == "completed"
    assert mock_service.audit_finish.await_args.kwargs["row_count"] == 1


def test_export_user_points_json_returns_array(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=True)
    rows = [
        {
            "id": "p1",
            "created_at": "2026-01-01T00:00:00",
            "externalUserId": "u1",
            "externalTaskId": "t1",
            "externalGameId": "g1",
            "points": 10,
            "caseName": "field_entry",
            "description": None,
            "idempotencyKey": None,
            "data": {"k": "v"},
            "apiKey_used": None,
        }
    ]
    mock_service = _make_mock_service(rows)
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/user-points" "?format=json&externalGameId=g1&limit=50",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    parsed = json.loads(response.content)
    assert parsed == rows

    audit_call = mock_service.audit_start.await_args
    assert audit_call.kwargs["dataset_type"] == "user-points"
    assert audit_call.kwargs["filters"].externalGameId == "g1"


def test_export_rejects_non_admin_with_403(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=False)
    mock_service = _make_mock_service([])
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/users?format=csv",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 403
    mock_service.audit_start.assert_not_called()


def test_export_rejects_limit_above_cap(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=True)
    mock_service = _make_mock_service([])
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/users?format=csv&limit=999999",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 422
    mock_service.audit_start.assert_not_called()


def test_export_history_returns_mapped_rows(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=True)
    from app.schema.export_schema import ExportAuditLogEntry

    entries = [
        ExportAuditLogEntry(
            id="audit-1",
            datasetType="users",
            format="csv",
            filters={"limit": 100},
            rowLimit=100,
            rowCount=42,
            status="completed",
            requestedBy="admin@example.com",
            created_at=None,
        )
    ]
    mock_service = AsyncMock()
    mock_service.list_history = AsyncMock(return_value=entries)
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/history?scope=mine&limit=25",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 200
    payload = response.json()
    assert payload == [
        {
            "id": "audit-1",
            "datasetType": "users",
            "format": "csv",
            "filters": {"limit": 100},
            "rowLimit": 100,
            "rowCount": 42,
            "status": "completed",
            "requestedBy": "admin@example.com",
            "created_at": None,
        }
    ]
    # scope=mine must scope to the calling admin's oauth_user_id
    call_kwargs = mock_service.list_history.await_args.kwargs
    assert call_kwargs["limit"] == 25
    assert call_kwargs["oauth_user_id"] == "admin-user"


def test_export_history_scope_all_drops_user_filter(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=True)
    mock_service = AsyncMock()
    mock_service.list_history = AsyncMock(return_value=[])
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/history?scope=all",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 200
    assert mock_service.list_history.await_args.kwargs["oauth_user_id"] is None


def test_export_history_rejects_non_admin(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=False)
    mock_service = AsyncMock()
    mock_service.list_history = AsyncMock(return_value=[])
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/history",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 403
    mock_service.list_history.assert_not_called()


def test_export_invalid_format_returns_422(test_client, monkeypatch):
    _patch_admin_auth(monkeypatch, is_admin=True)
    mock_service = _make_mock_service([])
    container.export_service.override(providers.Object(mock_service))

    try:
        response = test_client.get(
            "/api/v1/exports/users?format=parquet",
            headers={"Authorization": "Bearer mocked"},
        )
    finally:
        container.export_service.reset_override()

    assert response.status_code == 422

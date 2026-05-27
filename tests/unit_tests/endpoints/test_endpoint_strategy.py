from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import StreamingResponse

from app.api.v1.endpoints import strategy as strategy_endpoint
from app.core.exceptions import NotFoundError
from app.middlewares.auth_context import AuditLogger, AuthContext


def _audit(api_key="api-key-1", oauth_user_id=None):
    return AuditLogger(
        "strategies",
        MagicMock(),
        AuthContext(
            api_key=api_key,
            oauth_user_id=oauth_user_id,
            is_admin=False,
            token_data={"sub": oauth_user_id} if oauth_user_id else None,
        ),
    )


@pytest.mark.asyncio
async def test_get_strategy_list_with_token_creates_user_and_returns_strategies():
    service = MagicMock()
    expected = [{"id": "default", "name": "Default"}]
    service.list_all_strategies.return_value = expected

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await strategy_endpoint.get_strategy_list(
            service=service,
            audit=_audit(oauth_user_id="oauth-user-1"),
        )

    assert result == expected
    service.list_all_strategies.assert_called_once()
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_strategy_list_logs_error_and_raises_when_service_fails():
    service = MagicMock()
    service.list_all_strategies.side_effect = RuntimeError("list failed")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(RuntimeError, match="list failed"):
            await strategy_endpoint.get_strategy_list(
                service=service,
                audit=_audit(),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_by_id_success():
    service = MagicMock()
    expected = {"id": "default", "name": "Default"}
    service.list_all_strategies.return_value = [expected]

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        result = await strategy_endpoint.get_strategy_by_id(
            id="default",
            service=service,
            audit=_audit(oauth_user_id="oauth-user-2"),
        )

    assert result == expected
    service.list_all_strategies.assert_called_once()
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_strategy_by_id_raises_not_found_and_logs_error():
    service = MagicMock()
    service.list_all_strategies.return_value = [{"id": "other"}]

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(NotFoundError, match="Strategy not found with id: missing"):
            await strategy_endpoint.get_strategy_by_id(
                id="missing",
                service=service,
                audit=_audit(),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_graph_by_id_success_returns_streaming_response():
    service = MagicMock()
    service.get_strategy_by_id.return_value = {"id": "default"}
    dot = MagicMock()
    dot.pipe.return_value = b"png-bytes"
    strategy_instance = MagicMock()
    strategy_instance.generate_logic_graph.return_value = dot
    service.get_Class_by_id.return_value = strategy_instance

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        response = await strategy_endpoint.get_strategy_graph_by_id(
            id="default",
            service=service,
            audit=_audit(oauth_user_id="oauth-user-3"),
        )

    assert isinstance(response, StreamingResponse)
    assert response.media_type == "image/png"
    service.get_strategy_by_id.assert_called_once_with("default")
    service.get_Class_by_id.assert_called_once_with("default")
    strategy_instance.generate_logic_graph.assert_called_once_with(format="png")
    dot.pipe.assert_called_once_with(format="png")
    mock_add_log.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_strategy_graph_by_id_raises_when_strategy_not_found():
    service = MagicMock()
    service.get_strategy_by_id.return_value = None

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(NotFoundError, match="Strategy not found with id: missing"):
            await strategy_endpoint.get_strategy_graph_by_id(
                id="missing",
                service=service,
                audit=_audit(),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_graph_by_id_raises_when_class_not_found():
    service = MagicMock()
    service.get_strategy_by_id.return_value = {"id": "default"}
    service.get_Class_by_id.return_value = None

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(
            NotFoundError, match="No class found for strategy with id: default"
        ):
            await strategy_endpoint.get_strategy_graph_by_id(
                id="default",
                service=service,
                audit=_audit(),
            )

    assert mock_add_log.await_count == 2

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import StreamingResponse

from app.api.v1.endpoints import strategy as strategy_endpoint
from app.core.exceptions import NotFoundError


def _api_key_header(api_key="api-key-1"):
    return SimpleNamespace(data=SimpleNamespace(apiKey=api_key))


def _oauth_service(user_exists=True):
    service_oauth = MagicMock()
    service_oauth.get_user_by_sub.return_value = (
        SimpleNamespace(id="oauth-user-id") if user_exists else None
    )
    service_oauth.add = AsyncMock()
    return service_oauth


@pytest.mark.asyncio
async def test_get_strategy_list_with_token_creates_user_and_returns_strategies():
    service = MagicMock()
    expected = [{"id": "default", "name": "Default"}]
    service.list_all_strategies.return_value = expected
    service_oauth = _oauth_service(user_exists=False)

    with patch(
        "app.api.v1.endpoints.strategy.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(data={"sub": "oauth-user-1"})),
    ), patch("app.api.v1.endpoints.strategy.add_log", new=AsyncMock()) as mock_add_log:
        result = await strategy_endpoint.get_strategy_list(
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert result == expected
    service.list_all_strategies.assert_called_once()
    service_oauth.add.assert_awaited_once()
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_list_logs_error_and_raises_when_service_fails():
    service = MagicMock()
    service.list_all_strategies.side_effect = RuntimeError("list failed")

    with patch("app.api.v1.endpoints.strategy.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(RuntimeError, match="list failed"):
            await strategy_endpoint.get_strategy_list(
                service=service,
                service_log=MagicMock(),
                service_oauth=_oauth_service(),
                token=None,
                api_key_header=_api_key_header(),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_by_id_success():
    service = MagicMock()
    expected = {"id": "default", "name": "Default"}
    service.list_all_strategies.return_value = [expected]
    service_oauth = _oauth_service(user_exists=False)

    with patch(
        "app.api.v1.endpoints.strategy.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(data={"sub": "oauth-user-2"})),
    ), patch("app.api.v1.endpoints.strategy.add_log", new=AsyncMock()) as mock_add_log:
        result = await strategy_endpoint.get_strategy_by_id(
            id="default",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert result == expected
    service.list_all_strategies.assert_called_once()
    service_oauth.add.assert_awaited_once()
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_by_id_raises_not_found_and_logs_error():
    service = MagicMock()
    service.list_all_strategies.return_value = [{"id": "other"}]

    with patch("app.api.v1.endpoints.strategy.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(NotFoundError, match="Strategy not found with id: missing"):
            await strategy_endpoint.get_strategy_by_id(
                id="missing",
                service=service,
                service_log=MagicMock(),
                service_oauth=_oauth_service(),
                token=None,
                api_key_header=_api_key_header(),
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
    service_oauth = _oauth_service(user_exists=False)

    with patch(
        "app.api.v1.endpoints.strategy.valid_access_token",
        new=AsyncMock(return_value=SimpleNamespace(data={"sub": "oauth-user-3"})),
    ), patch("app.api.v1.endpoints.strategy.add_log", new=AsyncMock()) as mock_add_log:
        response = await strategy_endpoint.get_strategy_graph_by_id(
            id="default",
            service=service,
            service_log=MagicMock(),
            service_oauth=service_oauth,
            token="Bearer token",
            api_key_header=_api_key_header(),
        )

    assert isinstance(response, StreamingResponse)
    assert response.media_type == "image/png"
    service.get_strategy_by_id.assert_called_once_with("default")
    service.get_Class_by_id.assert_called_once_with("default")
    strategy_instance.generate_logic_graph.assert_called_once_with(format="png")
    dot.pipe.assert_called_once_with(format="png")
    service_oauth.add.assert_awaited_once()
    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_graph_by_id_raises_when_strategy_not_found():
    service = MagicMock()
    service.get_strategy_by_id.return_value = None

    with patch("app.api.v1.endpoints.strategy.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(NotFoundError, match="Strategy not found with id: missing"):
            await strategy_endpoint.get_strategy_graph_by_id(
                id="missing",
                service=service,
                service_log=MagicMock(),
                service_oauth=_oauth_service(),
                token=None,
                api_key_header=_api_key_header(),
            )

    assert mock_add_log.await_count == 2


@pytest.mark.asyncio
async def test_get_strategy_graph_by_id_raises_when_class_not_found():
    service = MagicMock()
    service.get_strategy_by_id.return_value = {"id": "default"}
    service.get_Class_by_id.return_value = None

    with patch("app.api.v1.endpoints.strategy.add_log", new=AsyncMock()) as mock_add_log:
        with pytest.raises(
            NotFoundError, match="No class found for strategy with id: default"
        ):
            await strategy_endpoint.get_strategy_graph_by_id(
                id="default",
                service=service,
                service_log=MagicMock(),
                service_oauth=_oauth_service(),
                token=None,
                api_key_header=_api_key_header(),
            )

    assert mock_add_log.await_count == 2

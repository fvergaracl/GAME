"""Sprint 7 - tests for ``GET /v1/strategies/{id}/schema``.

The endpoint inspects the built-in registry via ``StrategyService.
get_Class_by_id`` and shapes the response as a ``StrategySchema``
(ordered variables list with Python type names). The DSL_EXTEND editor
consumes this to render the "Parent overrides" toolbox category.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.endpoints import strategy as strategy_endpoint
from app.core.exceptions import NotFoundError
from app.middlewares.auth_context import AuditLogger, AuthContext


def _audit():
    return AuditLogger(
        "strategies",
        MagicMock(),
        AuthContext(
            api_key="api-key-1",
            oauth_user_id=None,
            is_admin=False,
            token_data=None,
        ),
    )


def _instance_mock(
    *,
    variables,
    name="Mock Strategy",
    description="desc",
    version="1.2.3",
    hash_version="ffeeddcc",
    strategy_id="mock_strategy"
):
    """Builds a MagicMock that quacks like a registered BaseStrategy.

    Only the methods the schema endpoint reaches into are stubbed -
    keeping the test honest about which surface of BaseStrategy is the
    contract for the new endpoint."""
    instance = MagicMock()
    instance.id = strategy_id
    instance.get_strategy_name.return_value = name
    instance.get_strategy_description.return_value = description
    instance.get_strategy_version.return_value = version
    instance.get_variables.return_value = variables
    instance._generate_hash_of_calculate_points.return_value = hash_version
    return instance


@pytest.mark.asyncio
async def test_get_schema_returns_typed_variables_ordered_by_name():
    service = MagicMock()
    service.get_Class_by_id.return_value = _instance_mock(
        variables={
            # Intentionally unordered + mixed types so the sort + type
            # inference are both exercised.
            "variable_bonus_points": 10,
            "variable_basic_points": 1,
            "variable_flag": True,
            "variable_factor": 1.5,
            "variable_label": "default",
            "variable_complex": {"k": "v"},
        },
    )

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        result = await strategy_endpoint.get_strategy_schema_by_id(
            id="mock_strategy",
            service=service,
            audit=_audit(),
        )

    # Variables sorted alphabetically - keeps UI rendering stable.
    names_in_order = [v.name for v in result.variables]
    assert names_in_order == sorted(names_in_order)

    # Type inference picks the right JSON-friendly label per Python type.
    by_name = {v.name: v for v in result.variables}
    assert by_name["variable_basic_points"].type == "int"
    assert by_name["variable_factor"].type == "float"
    assert by_name["variable_label"].type == "str"
    assert by_name["variable_flag"].type == "bool"  # NOT "int"
    assert by_name["variable_complex"].type == "dict"

    # currentValue carries the literal default from the built-in.
    assert by_name["variable_basic_points"].currentValue == 1
    assert by_name["variable_complex"].currentValue == {"k": "v"}

    # Top-level metadata flows through unchanged.
    assert result.id == "mock_strategy"
    assert result.name == "Mock Strategy"
    assert result.version == "1.2.3"
    assert result.hash_version == "ffeeddcc"


@pytest.mark.asyncio
async def test_get_schema_404s_when_strategy_not_in_registry():
    service = MagicMock()
    service.get_Class_by_id.side_effect = NotFoundError(
        detail="Strategy not found with id: unknown"
    )

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()):
        with pytest.raises(NotFoundError, match="Strategy not found"):
            await strategy_endpoint.get_strategy_schema_by_id(
                id="unknown",
                service=service,
                audit=_audit(),
            )

    service.get_Class_by_id.assert_called_once_with("unknown")


@pytest.mark.asyncio
async def test_get_schema_audits_failure_path():
    """Errors must be audited before re-raising so ops can trace what
    happened - mirrors the pattern used by the other strategy endpoints."""
    service = MagicMock()
    service.get_Class_by_id.side_effect = RuntimeError("boom")

    with patch("app.middlewares.auth_context.add_log", new=AsyncMock()) as add_log:
        with pytest.raises(RuntimeError, match="boom"):
            await strategy_endpoint.get_strategy_schema_by_id(
                id="x",
                service=service,
                audit=_audit(),
            )

    # The audit logger writes at least one ERROR-level entry on failure.
    # Be permissive about the audit shape; what we really care about is
    # that *some* logging happened in the error path.
    assert add_log.await_count >= 1

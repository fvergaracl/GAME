import io
from typing import List

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.container import Container
from app.core.exceptions import NotFoundError
from app.middlewares.auth_context import AuditLogger, audit_log
from app.schema.strategy_schema import Strategy, StrategySchema, StrategyVariableInfo
from app.services.strategy_service import StrategyService

router = APIRouter(
    prefix="/strategies",
    tags=["strategies"],
)

summary_get_strategies_list = "Retrieve Strategies List"
response_example_get_strategies_list = [
    {
        "id": "default",
        "name": "Default Strategy",
        "description": "Baseline adaptive scoring strategy.",
        "version": "1.0.0",
        "variables": {
            "variable_basic_points": 10,
            "bonus_multiplier": 1.2,
        },
        "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
    },
    {
        "id": "constantEffortStrategy",
        "name": "Constant Effort",
        "description": "Awards stable points for repeated behavior.",
        "version": "1.0.0",
        "variables": {
            "variable_basic_points": 5,
        },
        "hash_version": "f1a2c3d4e5f60987654321aabbccdde0",
    },
]

responses_get_strategies_list = {
    200: {
        "description": "Strategies retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_strategies_list}
        },
    },
    401: {
        "description": "Unauthorized: invalid bearer token when provided",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    500: {
        "description": "Internal server error while listing strategies",
    },
}

description_get_strategies_list = """
Returns all scoring strategies available in the engine.

### Authentication
- Supports `Authorization: Bearer <access_token>` and `X-API-Key`.
- Authentication is optional for read-only listing; when provided, user context is logged.

### Success (200)
Returns a list of strategies with:
- `id`
- `name`
- `description`
- `version`
- `variables`
- `hash_version`

### Error Cases
- `401`: invalid bearer token (when token is sent)
- `500`: strategy retrieval failure

<sub>**Id_endpoint:** `get_strategy_list`</sub>
"""  # noqa


@router.get(
    "",
    response_model=List[Strategy],
    summary=summary_get_strategies_list,
    description=description_get_strategies_list,
    responses=responses_get_strategies_list,
)
@inject
async def get_strategy_list(
    service: StrategyService = Depends(Provide[Container.strategy_service]),
    audit: AuditLogger = Depends(audit_log("strategies")),
):
    """
    Retrieve a list of all strategies.

    Args:
        service (StrategyService): Injected StrategyService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        List[Strategy]: The list of all strategies.
    """
    await audit.info("Get all strategies")
    try:
        return service.list_all_strategies()
    except Exception as e:
        await audit.error("Get all strategies failed", {"error": str(e)})
        raise e


summary_get_strategy_by_id = "Retrieve Strategy by ID"
response_example_get_strategy_by_id = {
    "id": "default",
    "name": "Default Strategy",
    "description": "Baseline adaptive scoring strategy.",
    "version": "1.0.0",
    "variables": {
        "variable_basic_points": 10,
        "bonus_multiplier": 1.2,
    },
    "hash_version": "9e6c5ce8f3fcb2a4f6b5b2f1c1d2a9f7",
}

responses_get_strategy_by_id = {
    200: {
        "description": "Strategy retrieved successfully",
        "content": {
            "application/json": {"example": response_example_get_strategy_by_id}
        },
    },
    401: {
        "description": "Unauthorized: invalid bearer token when provided",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    404: {
        "description": "Strategy not found for the provided id",
        "content": {
            "application/json": {
                "example": {"detail": "Strategy not found with id: default-v2"}
            }
        },
    },
    500: {
        "description": "Internal server error while retrieving strategy",
    },
}

description_get_strategy_by_id = """
Returns one strategy by its identifier.

### Path Parameter
- `id` (`string`): Unique strategy id (for example: `default`, `constantEffortStrategy`).

### Authentication
- Supports `Authorization: Bearer <access_token>` and `X-API-Key`.
- Authentication is optional for read-only retrieval; when provided, user context is logged.

### Success (200)
Returns the strategy object with:
- `id`
- `name`
- `description`
- `version`
- `variables`
- `hash_version`

### Error Cases
- `401`: invalid bearer token (when token is sent)
- `404`: no strategy found with the provided `id`
- `500`: strategy retrieval failure

<sub>**Id_endpoint:** `get_strategy_by_id`</sub>
"""  # noqa


@router.get(
    "/{id}",
    response_model=Strategy,
    summary=summary_get_strategy_by_id,
    description=description_get_strategy_by_id,
    responses=responses_get_strategy_by_id,
)
@inject
async def get_strategy_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
    audit: AuditLogger = Depends(audit_log("strategies")),
):
    """
    Retrieve a strategy by its ID.

    Args:
        id (str): The ID of the strategy.
        service (StrategyService): Injected StrategyService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        Strategy: The details of the specified strategy.
    """
    await audit.info("Get strategy by ID", {"id": id})
    all_strategies = service.list_all_strategies()
    try:
        for strategy in all_strategies:
            if strategy["id"] == id:
                return strategy
        raise NotFoundError(detail=f"Strategy not found with id: {id}")
    except Exception as e:
        await audit.error("Get strategy by ID failed", {"id": id, "error": str(e)})
        raise e


# --------------------------------------------------------------------------
# Sprint 7: /v1/strategies/{id}/schema
#
# Editor-facing endpoint that returns built-in metadata enriched with a
# typed, ordered variables list. The DSL_EXTEND editor (Blockly) uses
# this to populate the "Parent overrides" toolbox category and the
# read-only side panel describing the parent strategy.
# --------------------------------------------------------------------------

summary_get_strategy_schema_by_id = "Retrieve Strategy Schema by ID"
responses_get_strategy_schema_by_id = {
    200: {
        "description": (
            "Built-in strategy schema with typed variable metadata, "
            "consumed by the DSL_EXTEND editor."
        ),
    },
    401: {
        "description": "Unauthorized: invalid bearer token when provided",
    },
    404: {
        "description": "Strategy id not found in the built-in registry",
        "content": {
            "application/json": {
                "example": {"detail": "Strategy not found with id: unknown"}
            }
        },
    },
    500: {"description": "Internal server error while building schema"},
}

description_get_strategy_schema_by_id = """
Returns an editor-friendly schema of a built-in strategy.

Difference vs ``GET /v1/strategies/{id}``:
* ``variables`` is an **ordered list** (by name) instead of a dict so
  UI rendering is stable across calls.
* Each variable carries its Python type name (``int``, ``float``,
  ``str``, ``bool``, ``dict``, ``list``) so the editor can pick the
  right input widget when the DSL_EXTEND mode allows overriding it.

### Path Parameter
- `id` (`string`): Built-in strategy identifier (e.g. `default`).

### Authentication
- Supports `Authorization: Bearer <access_token>` and `X-API-Key`.

<sub>**Id_endpoint:** `get_strategy_schema_by_id`</sub>
"""  # noqa


# Python type → JSON-ish name we expose to the editor. We deliberately
# map ``NoneType`` to ``"null"`` because that's what JS callers will
# read it as; bool maps to itself (Python's bool inherits from int but
# we want the editor to render a checkbox, not a number input).
_TYPE_NAME_MAP = {
    bool: "bool",
    int: "int",
    float: "float",
    str: "str",
    dict: "dict",
    list: "list",
    type(None): "null",
}


def _variable_type_name(value) -> str:
    """Stable, JSON-friendly name for the variable's Python type."""
    return _TYPE_NAME_MAP.get(type(value), type(value).__name__)


@router.get(
    "/{id}/schema",
    response_model=StrategySchema,
    summary=summary_get_strategy_schema_by_id,
    description=description_get_strategy_schema_by_id,
    responses=responses_get_strategy_schema_by_id,
)
@inject
async def get_strategy_schema_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
    audit: AuditLogger = Depends(audit_log("strategies")),
):
    """
    Retrieve the editor schema for a built-in strategy.

    The lookup hits the in-process registry via ``get_Class_by_id`` (no
    DB round-trip) and inspects ``instance.get_variables()`` so the
    editor sees exactly what the built-in's ``__init__`` set up.
    """
    await audit.info("Get strategy schema by ID", {"id": id})
    try:
        instance = service.get_Class_by_id(id)
        variables_dict = instance.get_variables()
        variables = sorted(
            (
                StrategyVariableInfo(
                    name=name,
                    type=_variable_type_name(value),
                    currentValue=value,
                )
                for name, value in variables_dict.items()
            ),
            key=lambda v: v.name,
        )
        return StrategySchema(
            id=getattr(instance, "id", id),
            name=instance.get_strategy_name(),
            description=instance.get_strategy_description(),
            version=instance.get_strategy_version(),
            variables=variables,
            hash_version=instance._generate_hash_of_calculate_points(),
        )
    except Exception as e:
        await audit.error(
            "Get strategy schema by ID failed",
            {"id": id, "error": str(e)},
        )
        raise


summary_get_strategy_graph_by_id = "Retrieve Strategy Graph by ID"
responses_get_strategy_graph_by_id = {
    200: {
        "description": "Strategy logic graph rendered as PNG image",
        "content": {
            "image/png": {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            }
        },
    },
    401: {
        "description": "Unauthorized: invalid bearer token when provided",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid authentication credentials"}
            }
        },
    },
    404: {
        "description": "Strategy id not found or graph class unavailable",
        "content": {
            "application/json": {
                "example": {"detail": "Strategy not found with id: default-v2"}
            }
        },
    },
    500: {
        "description": "Internal server error while generating strategy graph",
    },
}

description_get_strategy_graph_by_id = """
Returns a visual representation of a strategy logic graph as a PNG image.

### Path Parameter
- `id` (`string`): Strategy identifier (for example: `default`).

### Authentication
- Supports `Authorization: Bearer <access_token>` and `X-API-Key`.
- Authentication is optional for read-only retrieval; when provided, user context is logged.

### Success (200)
- Content-Type: `image/png`
- Body: binary PNG payload with the generated strategy graph.

### Error Cases
- `401`: invalid bearer token (when token is sent)
- `404`: strategy not found or missing graph-capable class
- `500`: graph generation failure

<sub>**Id_endpoint:** `get_strategy_graph_by_id`</sub>
"""  # noqa


@router.get(
    "/{id}/graph",
    summary=summary_get_strategy_graph_by_id,
    description=description_get_strategy_graph_by_id,
    response_class=StreamingResponse,
    responses=responses_get_strategy_graph_by_id,
)
@inject
async def get_strategy_graph_by_id(
    id: str,
    service: StrategyService = Depends(Provide[Container.strategy_service]),
    audit: AuditLogger = Depends(audit_log("strategies")),
):
    """
    Retrieve a strategy graph by its ID.

    Args:
        id (str): The ID of the strategy.
        service (StrategyService): Injected StrategyService dependency.
        audit (AuditLogger): Per-request audit logger bound to the auth context.

    Returns:
        StreamingResponse: The logic graph of the specified strategy.
    """
    try:
        await audit.info("Get strategy graph by ID", {"id": id})
        strategy = service.get_strategy_by_id(id)
        if not strategy:
            raise NotFoundError(detail=f"Strategy not found with id: {id}")
        strategy_class = service.get_Class_by_id(id)
        if strategy_class is None:
            raise NotFoundError(detail=f"No class found for strategy with id: {id}")
        dot = strategy_class.generate_logic_graph(format="png")

        graph_png = dot.pipe(format="png")

        return StreamingResponse(io.BytesIO(graph_png), media_type="image/png")
    except Exception as e:
        await audit.error(
            "Get strategy graph by ID failed", {"id": id, "error": str(e)}
        )
        raise e

"""
Sprint 11 — wiring test: DslStrategy.calculate_points always invokes
the observer, exactly once, in both success and failure paths.

The observer is mocked so this test doesn't reach into Prometheus or
the database. The point is to pin the integration contract: every
execution flows through ``observer.record`` with the right shape, no
matter which branch of ``_calculate_dsl_full`` / ``_calculate_dsl_extend``
ran, and exceptions still propagate after the observer fires.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import DslExecutionError
from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy
from app.schema.strategy_definition_schema import StrategyDefinitionRead


def _read(astJson, *, strategy_type="DSL_FULL"):
    return StrategyDefinitionRead(
        id="def-1",
        realmId="realm-a",
        name="custom-1",
        description=None,
        type=strategy_type,
        parentStrategyId=None,
        astJson=astJson,
        blocklyXml=None,
        version=2,
        status="PUBLISHED",
        createdBy=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        publishedAt=datetime.now(timezone.utc),
        experimentTag=None,
    )


def _ast_basic():
    return {
        "type": "program",
        "id": "p",
        "rules": [
            {
                "type": "rule",
                "id": "r1",
                "when": {"type": "literal", "id": "lt", "value": True},
                "then": [
                    {
                        "type": "assign_points",
                        "id": "a1",
                        "value": {
                            "type": "literal",
                            "id": "lv",
                            "value": 7,
                        },
                        "case_name": "ObservedCase",
                    }
                ],
            },
        ],
    }


class TestDslStrategyObserverWiring(unittest.IsolatedAsyncioTestCase):
    async def test_observer_invoked_with_ok_result(self):
        observer = AsyncMock()
        analytics = MagicMock()
        interpreter = DslInterpreter(max_nodes=100, max_depth=8)

        strategy = DslStrategy(
            definition=_read(_ast_basic()),
            interpreter=interpreter,
            analytics_service=analytics,
            observer=observer,
        )
        result = await strategy.calculate_points(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            data={"x": 1},
        )

        self.assertEqual(result[0], 7)
        self.assertEqual(result[1], "ObservedCase")
        observer.record.assert_awaited_once()
        call_kwargs = observer.record.await_args.kwargs
        self.assertEqual(call_kwargs["status"], "ok")
        self.assertEqual(call_kwargs["errorCode"], None)
        self.assertEqual(call_kwargs["points"], 7.0)
        self.assertEqual(call_kwargs["caseName"], "ObservedCase")
        self.assertEqual(call_kwargs["strategyId"], "def-1")
        self.assertEqual(call_kwargs["strategyVersion"], 2)
        self.assertEqual(call_kwargs["strategyType"], "DSL_FULL")
        self.assertEqual(call_kwargs["realmId"], "realm-a")
        self.assertGreater(call_kwargs["durationMs"], 0.0)
        # The trace from the interpreter should make it through.
        self.assertIsNotNone(call_kwargs["trace"])
        self.assertGreater(call_kwargs["nodesExecuted"], 0)

    async def test_observer_invoked_on_dsl_execution_error(self):
        observer = AsyncMock()
        analytics = MagicMock()
        interpreter = DslInterpreter(max_nodes=100, max_depth=8)

        # Build an AST that divides by zero, which raises
        # DslExecutionError at runtime.
        ast = {
            "type": "program",
            "id": "p",
            "rules": [
                {
                    "type": "rule",
                    "id": "r1",
                    "when": {
                        "type": "literal", "id": "lt", "value": True,
                    },
                    "then": [
                        {
                            "type": "assign_points",
                            "id": "a1",
                            "value": {
                                "type": "arith",
                                "id": "ar",
                                "op": "/",
                                "left": {
                                    "type": "literal",
                                    "id": "ll",
                                    "value": 1,
                                },
                                "right": {
                                    "type": "literal",
                                    "id": "lr",
                                    "value": 0,
                                },
                            },
                            "case_name": "ShouldFail",
                        }
                    ],
                },
            ],
        }
        strategy = DslStrategy(
            definition=_read(ast),
            interpreter=interpreter,
            analytics_service=analytics,
            observer=observer,
        )
        with self.assertRaises(DslExecutionError):
            await strategy.calculate_points(
                externalGameId="g",
                externalTaskId="t",
                externalUserId="u",
                data={},
            )

        observer.record.assert_awaited_once()
        call_kwargs = observer.record.await_args.kwargs
        self.assertEqual(call_kwargs["status"], "error")
        self.assertEqual(
            call_kwargs["errorCode"], "DSL_ARITH_DIV_BY_ZERO"
        )
        self.assertIsNone(call_kwargs["points"])

    async def test_missing_observer_does_not_break_scoring(self):
        # Pre-Sprint-11 construction style: tests instantiate DslStrategy
        # without an observer. The execution path must remain unchanged.
        analytics = MagicMock()
        interpreter = DslInterpreter(max_nodes=100, max_depth=8)
        strategy = DslStrategy(
            definition=_read(_ast_basic()),
            interpreter=interpreter,
            analytics_service=analytics,
        )
        result = await strategy.calculate_points(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            data={},
        )
        self.assertEqual(result[0], 7)

    async def test_observer_failure_does_not_break_scoring(self):
        # An observer that raises in record() must not bubble up to the
        # scoring caller. Observability is best-effort.
        analytics = MagicMock()
        interpreter = DslInterpreter(max_nodes=100, max_depth=8)
        observer = AsyncMock()
        observer.record.side_effect = RuntimeError("metrics broken")
        strategy = DslStrategy(
            definition=_read(_ast_basic()),
            interpreter=interpreter,
            analytics_service=analytics,
            observer=observer,
        )
        result = await strategy.calculate_points(
            externalGameId="g",
            externalTaskId="t",
            externalUserId="u",
            data={},
        )
        self.assertEqual(result[0], 7)


if __name__ == "__main__":
    unittest.main()

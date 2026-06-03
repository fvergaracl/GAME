"""
Sprint 5 integration test — full path ``UserPointsService → StrategyService
→ DslStrategy`` for a ``custom:<uuid>`` task strategy.

This test does NOT spin up a database. It mocks ``StrategyDefinitionService.
get_strategy`` to return a ``StrategyDefinitionRead`` with the on-disk
``default_v0_0_2.json`` AST, then verifies that:

  1. ``UserPointsService.assign_points_to_user`` resolves a ``custom:``
     strategy id through the new async ``get_strategy_instance``.
  2. The DSL interpreter actually runs (returns the expected case_name).
  3. ``StrategyDefinitionService.get_strategy`` is awaited with the
     correct ``realmId`` — the multi-tenant isolation property the
     roadmap calls out as the highest-impact risk.

The reason for not using the in-memory aiosqlite conftest is that the
wiring under test is the resolver + DSL execution, not the persistence
layer (already covered by the dedicated strategy_definition tests). A
pure-mock setup runs in milliseconds and isolates the failure mode.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.engine.dsl_interpreter import DslInterpreter
from app.schema.strategy_definition_schema import StrategyDefinitionRead
from app.services.strategy_service import StrategyService
from app.services.user_points_service import UserPointsService

_AST_PATH = (
    Path(__file__).resolve().parents[3]
    / "app"
    / "engine"
    / "dsl_templates"
    / "default_v0_0_2.json"
)
_AST = json.loads(_AST_PATH.read_text(encoding="utf-8"))


class TestUserPointsServiceDslWiring(unittest.IsolatedAsyncioTestCase):
    GAME_UUID = "00000000-0000-0000-0000-000000000001"
    CUSTOM_STRATEGY_UUID = "abc-12345"
    API_KEY = "apikey-realm-tenant-a"

    def setUp(self) -> None:
        # ----- repositories: same mock pattern as test_user_points_service.py
        self.user_points_repository = AsyncMock()
        self.users_repository = AsyncMock()
        self.users_game_config_repository = AsyncMock()
        self.game_repository = AsyncMock()
        self.task_repository = AsyncMock()
        self.wallet_repository = AsyncMock()
        self.wallet_transaction_repository = AsyncMock()
        self._db_session = MagicMock()
        self._db_session.commit = AsyncMock()
        self._db_session.rollback = AsyncMock()
        self._db_session.flush = AsyncMock()
        self._db_session.close = AsyncMock()
        self._session_context = MagicMock()
        self._session_context.__aenter__ = AsyncMock(return_value=self._db_session)
        self._session_context.__aexit__ = AsyncMock(return_value=False)
        self.user_points_repository.session_factory = MagicMock(
            return_value=self._session_context
        )
        self.user_points_repository.read_by_user_task_and_idempotency = AsyncMock(
            return_value=None
        )
        self.user_points_repository.create = AsyncMock(
            return_value=SimpleNamespace(
                id="userpoints-1", created_at="2026-05-27T00:00:00"
            )
        )
        self.wallet_repository.upsert_points_balance = AsyncMock(
            return_value=SimpleNamespace(id="wallet-1", pointsBalance=1)
        )
        self.wallet_transaction_repository.create = AsyncMock(
            return_value=SimpleNamespace(id="txn-1")
        )

        # ----- strategy_definition_service: returns the on-disk AST
        self.definition_service = MagicMock()
        self.definition_service.get_strategy = AsyncMock(
            return_value=StrategyDefinitionRead(
                id=self.CUSTOM_STRATEGY_UUID,
                realmId=self.API_KEY,
                name="default_via_dsl",
                description="Parity DSL of EnhancedGamificationStrategy.",
                type="DSL_FULL",
                astJson=_AST,
                version=1,
                status="PUBLISHED",
            )
        )

        # ----- analytics service: configure all 6 methods as AsyncMocks so
        # ExecutionContext.build_for_ast can await them. ``task=1`` triggers
        # rule 1 (BasicEngagement) so the test asserts the simplest branch.
        self.analytics_service = MagicMock()
        for method, value in {
            "count_measurements_by_external_task_id": 1,
            "get_user_task_measurements_count": 0,
            "get_avg_time_between_tasks_by_user_and_game_task": 0,
            "get_avg_time_between_tasks_for_all_users": 0,
            "get_last_window_time_diff": 0,
            "get_new_last_window_time_diff": 0,
        }.items():
            setattr(self.analytics_service, method, AsyncMock(return_value=value))

        # ----- strategy_service: real instance with mocks injected. This is
        # the wiring under test — we exercise the production constructor.
        self.strategy_service = StrategyService(
            strategy_definition_service=self.definition_service,
            dsl_interpreter=DslInterpreter(max_nodes=1000, max_depth=32),
            analytics_service=self.analytics_service,
        )

        # ----- the system under test
        self.service = UserPointsService(
            user_points_repository=self.user_points_repository,
            users_repository=self.users_repository,
            users_game_config_repository=self.users_game_config_repository,
            game_repository=self.game_repository,
            task_repository=self.task_repository,
            wallet_repository=self.wallet_repository,
            wallet_transaction_repository=self.wallet_transaction_repository,
            strategy_service=self.strategy_service,
        )

        # ----- typical happy-path game/task/user resolution
        self.game_repository.read_by_column.return_value = SimpleNamespace(
            id="game-1", externalGameId="external-game-1"
        )
        self.task_repository.read_by_gameId_and_externalTaskId.return_value = (
            SimpleNamespace(
                id="task-1",
                strategyId=f"custom:{self.CUSTOM_STRATEGY_UUID}",
            )
        )
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id="user-1", externalUserId="user_1"
        )

    async def test_assign_points_with_custom_strategy_runs_dsl_and_scopes_realm(self):
        """
        Custom strategy id resolves through the new async path, the DSL
        interpreter runs against the AST and the analytics mocks, and
        the persisted points + caseName reflect the DSL's first matching
        rule (BasicEngagement).
        """
        schema = SimpleNamespace(externalUserId="user_1", data={})

        response = await self.service.assign_points_to_user(
            self.GAME_UUID,
            "task-external-1",
            schema,
            False,
            self.API_KEY,
        )

        # The DSL fired rule 1 (task.measurements_count < 2) → 1 point,
        # "BasicEngagement". The Python ``EnhancedGamificationStrategy``
        # would produce the same output for the same inputs (proven by
        # ``tests/unit_tests/engine/test_default_dsl_parity.py``).
        self.assertEqual(response.points, 1)
        self.assertEqual(response.caseName, "BasicEngagement")

        # Multi-tenant isolation: the resolver must scope the strategy
        # fetch by realmId derived from the API key. A bug here would
        # let tenant A invoke tenant B's strategy.
        self.definition_service.get_strategy.assert_awaited_once_with(
            id=self.CUSTOM_STRATEGY_UUID, realmId=self.API_KEY
        )

        # Sanity: the DSL did read the one analytics path it needed and
        # short-circuited before any others mattered. ``user.measurements_count``
        # is referenced by rule 2 so its analytic is also precomputed by
        # ``ExecutionContext.build_for_ast`` even though rule 2 never runs.
        self.analytics_service.count_measurements_by_external_task_id.assert_awaited_once()

    async def test_assign_points_with_custom_strategy_in_wrong_realm_404s(self):
        """
        If the strategy lives in realm A and the caller authenticates
        with realm B's API key, the repository-level filter in
        ``StrategyDefinitionService.get_strategy`` returns nothing and
        ``UserPointsService`` surfaces a NotFoundError. This is the
        backbone of the multi-tenant guarantee.
        """
        from app.core.exceptions import NotFoundError

        # Simulate the repository miss the realm-scoped query would
        # produce when the strategy belongs to another tenant.
        self.definition_service.get_strategy = AsyncMock(
            side_effect=NotFoundError(detail="Custom strategy not found")
        )

        schema = SimpleNamespace(externalUserId="user_1", data={})

        with self.assertRaises(NotFoundError):
            await self.service.assign_points_to_user(
                self.GAME_UUID,
                "task-external-1",
                schema,
                False,
                "wrong-realm-key",
            )

        self.definition_service.get_strategy.assert_awaited_once_with(
            id=self.CUSTOM_STRATEGY_UUID, realmId="wrong-realm-key"
        )

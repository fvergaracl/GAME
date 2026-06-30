"""
Executable recipe for the citizen-science domain (S3.1).

This module is the runnable proof behind the "Recipe for the real domain"
docs section. It authors a custom DSL_FULL strategy - a real strategy, not
the ``default`` built-in - and drives it through the production engine
(``DslStrategy`` -> ``ExecutionContext`` -> ``DslInterpreter``) against a
real ``UserPointsRepository`` + ``UserPointsAnalyticsService`` backed by an
isolated SQLite database. No HTTP, no Keycloak, no Postgres container, so
the output is deterministic and reproducible.

The strategy mirrors how socio_bee / greengage reward field measurements,
walking the three scoring moments the recipe documents:

* a completed task (onboarding award, driven by the real
  ``task.measurements_count`` analytics field read from the DB),
* a priority-zone bonus (driven by the per-event ``data.priority_zone``),
* a streak bonus (driven by ``data.streak_days``, capped with ``clamp``).

Why a DSL strategy and not socio_bee directly: the built-in
``SocioBeeStrategy`` (and ``default.py``'s ``EnhancedGamificationStrategy``
it shares logic with) call the *async* analytics service methods without
``await``, so they only run against a synchronous mock - against the real
service they raise ``TypeError: '<' not supported between instances of
'coroutine' and 'int'``. A DSL strategy resolves the same whitelisted
analytics fields through ``ExecutionContext.build_for_ast``, which awaits
them correctly, so it is the reproducible vehicle for a real end-to-end run.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlmodel import SQLModel

from app.engine.dsl_interpreter import DslInterpreter
from app.engine.dsl_strategy import DslStrategy
from app.engine.dsl_validator import validate_ast
from app.model.games import Games
from app.model.tasks import Tasks
from app.model.user_points import UserPoints
from app.model.users import Users
from app.repository.user_points_repository import UserPointsRepository
from app.schema.strategy_definition_schema import StrategyDefinitionRead
from app.services.user_points_analytics_service import UserPointsAnalyticsService


@compiles(PG_UUID, "sqlite")
def _compile_uuid_for_sqlite(_type, _compiler, **_kw):
    # SQLite has no native UUID type; store the Postgres UUID columns as CHAR.
    return "CHAR(36)"


@compiles(PG_JSONB, "sqlite")
def _compile_jsonb_for_sqlite(_type, _compiler, **_kw):
    # SQLite has no native JSONB type; store the Postgres JSONB columns as JSON.
    return "JSON"


# Citizen-science scoring program. Rules are evaluated top-to-bottom; the
# first match wins, otherwise ``default`` runs. Every field path used here is
# in the dsl_ast.py whitelist: ``task.measurements_count`` is an analytics
# field resolved from the DB, ``data.priority_zone`` / ``data.streak_days``
# are per-event payload values.
CITIZEN_SCIENCE_AST = {
    "type": "program",
    "rules": [
        # Moment 1 - completed task (onboarding). Until the task has two
        # recorded measurements, award a flat onboarding bonus. Reads a REAL
        # analytics field counted from the user_points table.
        {
            "type": "rule",
            "when": {
                "type": "compare",
                "op": "<",
                "left": {"type": "field", "path": "task.measurements_count"},
                "right": {"type": "literal", "value": 2},
            },
            "then": [
                {
                    "type": "assign_points",
                    "value": {"type": "literal", "value": 5},
                    "case_name": "TaskCompleted-Onboarding",
                }
            ],
        },
        # Moment 2 - priority-zone bonus. The event flags a high-priority
        # measurement zone; award base + zone bonus (10 + 15).
        {
            "type": "rule",
            "when": {
                "type": "compare",
                "op": "==",
                "left": {"type": "field", "path": "data.priority_zone"},
                "right": {"type": "literal", "value": 1},
            },
            "then": [
                {
                    "type": "assign_points",
                    "value": {
                        "type": "arith",
                        "op": "+",
                        "left": {"type": "literal", "value": 10},
                        "right": {"type": "literal", "value": 15},
                    },
                    "case_name": "PriorityZoneBonus",
                }
            ],
        },
        # Moment 3 - streak bonus. data.streak_days drives an escalating
        # reward (5 points per consecutive day) capped at 50 with clamp().
        {
            "type": "rule",
            "when": {
                "type": "compare",
                "op": ">=",
                "left": {"type": "field", "path": "data.streak_days"},
                "right": {"type": "literal", "value": 3},
            },
            "then": [
                {
                    "type": "assign_points",
                    "value": {
                        "type": "func_call",
                        "name": "clamp",
                        "args": [
                            {
                                "type": "arith",
                                "op": "*",
                                "left": {"type": "field", "path": "data.streak_days"},
                                "right": {"type": "literal", "value": 5},
                            },
                            {"type": "literal", "value": 0},
                            {"type": "literal", "value": 50},
                        ],
                    },
                    "case_name": "StreakBonus",
                }
            ],
        },
    ],
    # Fallback - a completed task with history but no special flag.
    "default": {
        "type": "assign_points",
        "value": {"type": "literal", "value": 2},
        "case_name": "TaskCompleted",
    },
}


GAME = "greengage_field_campaign"
TASK = "air_quality_measurement"
USER = "citizen_ada"


class _RecipeDatabase:
    """Minimal async DB wrapper exposing ``async with db.session()`` - the
    same contract repository providers expect in production."""

    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(db_url, future=True)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def create_all(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        session = self._session_factory()
        try:
            yield session
        finally:
            await session.close()

    async def dispose(self) -> None:
        await self._engine.dispose()


def _build_strategy(analytics: UserPointsAnalyticsService) -> DslStrategy:
    validate_ast(CITIZEN_SCIENCE_AST)
    definition = StrategyDefinitionRead(
        id="recipe-citizen-science",
        realmId=None,
        name="citizen_science_demo",
        description="socio_bee-style priority-zone + streak DSL strategy",
        type="DSL_FULL",
        astJson=CITIZEN_SCIENCE_AST,
        version=1,
        status="PUBLISHED",
    )
    interpreter = DslInterpreter(max_nodes=1000, max_depth=32)
    return DslStrategy(
        definition=definition,
        interpreter=interpreter,
        analytics_service=analytics,
    )


async def test_citizen_science_recipe_walks_all_scoring_moments():
    """Drive the custom DSL strategy through a completed task, a bonus and a
    streak, asserting the exact (points, caseName) the recipe documents."""
    db = _RecipeDatabase("sqlite+aiosqlite:///:memory:")
    await db.create_all()
    try:
        repository = UserPointsRepository(session_factory=db.session)
        analytics = UserPointsAnalyticsService(repository)
        strategy = _build_strategy(analytics)

        async with db.session() as session:
            game = Games(
                externalGameId=GAME,
                strategyId="custom:recipe-citizen-science",
                platform="mobile",
            )
            session.add(game)
            await session.flush()
            task = Tasks(
                externalTaskId=TASK,
                gameId=game.id,
                strategyId="custom:recipe-citizen-science",
                status="open",
            )
            session.add(task)
            await session.flush()
            user = Users(externalUserId=USER)
            session.add(user)
            await session.flush()
            user_id, task_id = user.id, task.id
            await session.commit()

        async def score(data):
            return await strategy.calculate_points(
                externalGameId=GAME,
                externalTaskId=TASK,
                externalUserId=USER,
                data=data,
            )

        # Moment 1 - completed task, no history yet: task.measurements_count
        # is 0 (< 2), so the onboarding rule wins.
        assert await score({"priority_zone": 0, "streak_days": 0}) == (
            5,
            "TaskCompleted-Onboarding",
        )

        # Record two historical measurements at fixed timestamps so
        # task.measurements_count >= 2 from now on (the onboarding rule stops
        # matching). Timestamps are explicit; nothing reads the wall clock.
        base = datetime(2026, 6, 30, 8, 0, 0, tzinfo=timezone.utc)
        async with db.session() as session:
            for offset in range(2):
                session.add(
                    UserPoints(
                        points=5,
                        caseName="TaskCompleted-Onboarding",
                        data={},
                        description="seeded history",
                        userId=user_id,
                        taskId=task_id,
                        created_at=base + timedelta(minutes=offset),
                    )
                )
            await session.commit()

        # Moment 2 - priority-zone bonus (10 + 15).
        assert await score({"priority_zone": 1, "streak_days": 0}) == (
            25,
            "PriorityZoneBonus",
        )

        # Moment 3 - streak bonus, day 4: 4 * 5 = 20, under the cap.
        assert await score({"priority_zone": 0, "streak_days": 4}) == (
            20,
            "StreakBonus",
        )

        # Moment 3 (capped) - day 20: 20 * 5 = 100, clamped to 50.
        assert await score({"priority_zone": 0, "streak_days": 20}) == (
            50,
            "StreakBonus",
        )

        # Fallback - completed task with history, no special flag.
        assert await score({"priority_zone": 0, "streak_days": 0}) == (
            2,
            "TaskCompleted",
        )
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - convenience runner
    import asyncio
    import json

    async def _demo():
        db = _RecipeDatabase("sqlite+aiosqlite:///:memory:")
        await db.create_all()
        repository = UserPointsRepository(session_factory=db.session)
        analytics = UserPointsAnalyticsService(repository)
        strategy = _build_strategy(analytics)
        async with db.session() as session:
            game = Games(
                externalGameId=GAME,
                strategyId="custom:recipe-citizen-science",
                platform="mobile",
            )
            session.add(game)
            await session.flush()
            task = Tasks(
                externalTaskId=TASK,
                gameId=game.id,
                strategyId="custom:recipe-citizen-science",
                status="open",
            )
            session.add(task)
            await session.flush()
            user = Users(externalUserId=USER)
            session.add(user)
            await session.flush()
            user_id, task_id = user.id, task.id
            await session.commit()

        async def score(label, data):
            result = await strategy.calculate_points(
                externalGameId=GAME, externalTaskId=TASK, externalUserId=USER, data=data
            )
            print(f"{label}: data={json.dumps(data)} -> {result}")

        await score("E1 completed (no history)", {"priority_zone": 0, "streak_days": 0})
        base = datetime(2026, 6, 30, 8, 0, 0, tzinfo=timezone.utc)
        async with db.session() as session:
            for offset in range(2):
                session.add(
                    UserPoints(
                        points=5,
                        caseName="TaskCompleted-Onboarding",
                        data={},
                        description="seeded history",
                        userId=user_id,
                        taskId=task_id,
                        created_at=base + timedelta(minutes=offset),
                    )
                )
            await session.commit()
        await score("E2 priority zone", {"priority_zone": 1, "streak_days": 0})
        await score("E3 streak day 4", {"priority_zone": 0, "streak_days": 4})
        await score("E4 streak day 20", {"priority_zone": 0, "streak_days": 20})
        await score("E5 plain completed", {"priority_zone": 0, "streak_days": 0})
        await db.dispose()

    asyncio.run(_demo())

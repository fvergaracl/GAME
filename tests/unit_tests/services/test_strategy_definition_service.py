"""
Unit tests for :class:`StrategyDefinitionService`.

These exercise the versioning / lifecycle rules in isolation using a
hand-rolled fake repository - the underlying repository is covered by
integration tests separately. The fake is intentionally tiny (just
enough state to drive the service's branches) so the test reads like a
spec for the service's behaviour.
"""

import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Dict, List, Optional

from app.core.exceptions import (BadRequestError, ConflictError, DuplicatedError,
                                 NotFoundError)
from app.model.strategy_definition import (StrategyDefinitionStatus,
                                           StrategyDefinitionType)
from app.schema.strategy_definition_schema import (StrategyDefinitionCreate,
                                                   StrategyDefinitionUpdate)
from app.services.strategy_definition_service import StrategyDefinitionService


class FakeStrategyDefinitionRepository:
    """
    Minimal in-memory stand-in for the repository.

    Keeps rows in a dict keyed by id; the few helpers the service calls
    walk the dict directly. This avoids a real Postgres in unit tests
    while still exercising the service's branching logic.
    """

    def __init__(self):
        self._rows: Dict[str, SimpleNamespace] = {}

    async def list_for_realm(
        self,
        *,
        realmId: Optional[str],
        status: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> List[SimpleNamespace]:
        out = [
            r
            for r in self._rows.values()
            if r.realmId == realmId
            and (status is None or r.status == status)
            and (type is None or r.type == type)
        ]
        out.sort(key=lambda r: (r.name, -r.version))
        return out[:limit]

    async def get_for_realm(
        self, *, id: str, realmId: Optional[str]
    ) -> Optional[SimpleNamespace]:
        row = self._rows.get(id)
        if row is None or row.realmId != realmId:
            return None
        return row

    async def list_versions(
        self, *, realmId: Optional[str], name: str
    ) -> List[SimpleNamespace]:
        return sorted(
            [r for r in self._rows.values() if r.realmId == realmId and r.name == name],
            key=lambda r: -r.version,
        )

    async def get_max_version(self, *, realmId: Optional[str], name: str) -> int:
        versions = [
            r.version
            for r in self._rows.values()
            if r.realmId == realmId and r.name == name
        ]
        return max(versions) if versions else 0

    async def get_published(
        self, *, realmId: Optional[str], name: str
    ) -> Optional[SimpleNamespace]:
        for r in self._rows.values():
            if (
                r.realmId == realmId
                and r.name == name
                and r.status == StrategyDefinitionStatus.PUBLISHED.value
            ):
                return r
        return None

    async def get_version(
        self, *, realmId: Optional[str], name: str, version: int
    ) -> Optional[SimpleNamespace]:
        for r in self._rows.values():
            if r.realmId == realmId and r.name == name and r.version == version:
                return r
        return None

    async def set_status(
        self,
        *,
        id: str,
        status: str,
        publishedAt: Optional[datetime] = None,
    ) -> None:
        row = self._rows[id]
        row.status = status
        if publishedAt is not None:
            row.publishedAt = publishedAt

    async def create(self, schema) -> SimpleNamespace:
        row_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        data = schema.model_dump()
        row = SimpleNamespace(
            id=row_id,
            created_at=now,
            updated_at=now,
            **data,
        )
        self._rows[row_id] = row
        return row

    async def update(self, id, schema) -> SimpleNamespace:
        row = self._rows[id]
        patch = schema.model_dump(exclude_none=True)
        # `type` arrives as an enum from StrategyDefinitionUpdate; persist
        # the string value to match how the real repo stores it.
        if "type" in patch and hasattr(patch["type"], "value"):
            patch["type"] = patch["type"].value
        for k, v in patch.items():
            setattr(row, k, v)
        row.updated_at = datetime.now(timezone.utc)
        return row


class _Base(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = FakeStrategyDefinitionRepository()
        self.service = StrategyDefinitionService(
            strategy_definition_repository=self.repo
        )


class TestCreate(_Base):
    async def test_create_persists_initial_draft(self):
        payload = StrategyDefinitionCreate(
            name="onboarding-boost",
            description="Reward new users for first task.",
            type=StrategyDefinitionType.DSL_FULL,
            astJson={"type": "program", "rules": []},
        )

        result = await self.service.create(
            payload=payload,
            realmId="realm-a",
            createdBy="user-1",
            apiKey_used=None,
            oauth_user_id="user-1",
        )

        self.assertEqual(result.name, "onboarding-boost")
        self.assertEqual(result.version, 1)
        self.assertEqual(result.status, StrategyDefinitionStatus.DRAFT.value)
        self.assertEqual(result.realmId, "realm-a")
        self.assertEqual(result.type, StrategyDefinitionType.DSL_FULL.value)
        # validate_ast may have backfilled `id` deterministically; assert
        # on the shape, not on byte-for-byte equality.
        self.assertEqual(result.astJson["type"], "program")
        self.assertEqual(result.astJson["rules"], [])

    async def test_create_rejects_duplicate_name_in_same_realm(self):
        payload = StrategyDefinitionCreate(
            name="duplicated",
            type=StrategyDefinitionType.DSL_FULL,
        )
        await self.service.create(
            payload=payload,
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        with self.assertRaises(DuplicatedError):
            await self.service.create(
                payload=payload,
                realmId="realm-a",
                createdBy=None,
                apiKey_used=None,
                oauth_user_id=None,
            )

    async def test_same_name_allowed_across_realms(self):
        payload = StrategyDefinitionCreate(
            name="shared",
            type=StrategyDefinitionType.DSL_FULL,
        )
        await self.service.create(
            payload=payload,
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        # Another realm should be free to reuse the same name.
        result = await self.service.create(
            payload=payload,
            realmId="realm-b",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        self.assertEqual(result.realmId, "realm-b")
        self.assertEqual(result.version, 1)

    async def test_create_dsl_extend_requires_parent(self):
        payload = StrategyDefinitionCreate(
            name="needs-parent",
            type=StrategyDefinitionType.DSL_EXTEND,
        )
        with self.assertRaises(BadRequestError):
            await self.service.create(
                payload=payload,
                realmId="realm-a",
                createdBy=None,
                apiKey_used=None,
                oauth_user_id=None,
            )

    async def test_create_dsl_full_rejects_parent(self):
        payload = StrategyDefinitionCreate(
            name="no-parent-allowed",
            type=StrategyDefinitionType.DSL_FULL,
            parentStrategyId="default",
        )
        with self.assertRaises(BadRequestError):
            await self.service.create(
                payload=payload,
                realmId="realm-a",
                createdBy=None,
                apiKey_used=None,
                oauth_user_id=None,
            )


class TestTenantIsolation(_Base):
    async def test_get_returns_404_when_row_belongs_to_other_realm(self):
        payload = StrategyDefinitionCreate(
            name="hidden", type=StrategyDefinitionType.DSL_FULL
        )
        created = await self.service.create(
            payload=payload,
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        with self.assertRaises(NotFoundError):
            await self.service.get_strategy(id=created.id, realmId="realm-b")

    async def test_list_only_returns_rows_for_caller_realm(self):
        for realm in ("realm-a", "realm-b"):
            await self.service.create(
                payload=StrategyDefinitionCreate(
                    name=f"strat-{realm}",
                    type=StrategyDefinitionType.DSL_FULL,
                ),
                realmId=realm,
                createdBy=None,
                apiKey_used=None,
                oauth_user_id=None,
            )

        listed = await self.service.list_strategies(realmId="realm-a")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].name, "strat-realm-a")


class TestVersioning(_Base):
    async def _create_and_publish(self) -> str:
        created = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="evolving",
                type=StrategyDefinitionType.DSL_FULL,
                astJson={"type": "program", "rules": []},
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        await self.service.publish(id=created.id, realmId="realm-a")
        return created.id

    async def test_updating_draft_mutates_in_place(self):
        created = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="draft-edit",
                type=StrategyDefinitionType.DSL_FULL,
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        result = await self.service.update(
            id=created.id,
            payload=StrategyDefinitionUpdate(description="updated"),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        self.assertEqual(result.id, created.id)
        self.assertEqual(result.version, 1)
        self.assertEqual(result.description, "updated")
        self.assertEqual(result.status, StrategyDefinitionStatus.DRAFT.value)

    async def test_updating_published_forks_new_draft(self):
        published_id = await self._create_and_publish()

        v2_ast = {
            "type": "program",
            "rules": [],
            "default": {
                "type": "assign_points",
                "value": {"type": "literal", "value": 2},
                "case_name": "v2",
            },
        }
        forked = await self.service.update(
            id=published_id,
            payload=StrategyDefinitionUpdate(astJson=v2_ast),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        self.assertNotEqual(forked.id, published_id)
        self.assertEqual(forked.version, 2)
        self.assertEqual(forked.status, StrategyDefinitionStatus.DRAFT.value)
        # The fork carries the new AST (validator auto-assigned ids).
        self.assertEqual(forked.astJson["default"]["case_name"], "v2")

        # Published row is untouched.
        original = await self.service.get_strategy(id=published_id, realmId="realm-a")
        self.assertEqual(original.status, StrategyDefinitionStatus.PUBLISHED.value)
        self.assertNotIn("default", original.astJson)

    async def test_archived_rows_are_immutable(self):
        created = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="archive-me",
                type=StrategyDefinitionType.DSL_FULL,
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        await self.service.archive(id=created.id, realmId="realm-a")

        with self.assertRaises(ConflictError):
            await self.service.update(
                id=created.id,
                payload=StrategyDefinitionUpdate(description="too late"),
                realmId="realm-a",
                createdBy=None,
                apiKey_used=None,
                oauth_user_id=None,
            )


class TestPublishLifecycle(_Base):
    async def test_publish_archives_previous_published_sibling(self):
        # Create + publish v1.
        v1 = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="rotating",
                type=StrategyDefinitionType.DSL_FULL,
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        await self.service.publish(id=v1.id, realmId="realm-a")

        # Editing the published row forks a draft v2.
        v2 = await self.service.update(
            id=v1.id,
            payload=StrategyDefinitionUpdate(description="v2"),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        # Publish v2 - should archive v1.
        await self.service.publish(id=v2.id, realmId="realm-a")

        archived_v1 = await self.service.get_strategy(id=v1.id, realmId="realm-a")
        live_v2 = await self.service.get_strategy(id=v2.id, realmId="realm-a")
        self.assertEqual(archived_v1.status, StrategyDefinitionStatus.ARCHIVED.value)
        self.assertEqual(live_v2.status, StrategyDefinitionStatus.PUBLISHED.value)

    async def test_publish_is_idempotent(self):
        created = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="idempotent",
                type=StrategyDefinitionType.DSL_FULL,
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        first = await self.service.publish(id=created.id, realmId="realm-a")
        again = await self.service.publish(id=created.id, realmId="realm-a")
        self.assertEqual(first.id, again.id)
        self.assertEqual(again.status, StrategyDefinitionStatus.PUBLISHED.value)

    async def test_cannot_publish_archived(self):
        created = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="no-resurrect",
                type=StrategyDefinitionType.DSL_FULL,
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        await self.service.archive(id=created.id, realmId="realm-a")
        with self.assertRaises(ConflictError):
            await self.service.publish(id=created.id, realmId="realm-a")


class TestNameExists(_Base):
    """Sprint 8: the import endpoint relies on ``name_exists`` to decide
    whether to auto-rename the incoming bundle. The helper must be
    tenant-scoped (a name colliding in realm A must not stop an import
    into realm B) and must consider every version of a family."""

    async def test_name_exists_is_false_for_unknown_name(self):
        self.assertFalse(await self.service.name_exists(realmId="realm-a", name="nada"))

    async def test_name_exists_is_true_after_create(self):
        await self.service.create(
            payload=StrategyDefinitionCreate(
                name="taken",
                type=StrategyDefinitionType.DSL_FULL,
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        self.assertTrue(await self.service.name_exists(realmId="realm-a", name="taken"))

    async def test_name_exists_is_tenant_scoped(self):
        await self.service.create(
            payload=StrategyDefinitionCreate(
                name="shared",
                type=StrategyDefinitionType.DSL_FULL,
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        self.assertFalse(
            await self.service.name_exists(realmId="realm-b", name="shared")
        )


class FakeAssignmentRepository:
    """
    Stand-in for ``GameRepository`` / ``TaskRepository`` exposing just
    the two methods :meth:`StrategyDefinitionService.rollback` calls on
    them. Each instance keeps a list of (strategyId,) tuples so the
    test can assert the cascade actually rewrote them.
    """

    def __init__(self, rows: Optional[List[str]] = None):
        # rows is a list of strategyId values (one per Games/Tasks row).
        self.rows: List[str] = list(rows or [])
        self.bulk_calls: List[Dict[str, str]] = []

    async def list_by_strategy_id(self, strategy_id: str):
        return [SimpleNamespace(strategyId=s) for s in self.rows if s == strategy_id]

    async def bulk_update_strategy_id(
        self, *, old_strategy_id: str, new_strategy_id: str
    ) -> int:
        self.bulk_calls.append({"old": old_strategy_id, "new": new_strategy_id})
        count = 0
        for i, current in enumerate(self.rows):
            if current == old_strategy_id:
                self.rows[i] = new_strategy_id
                count += 1
        return count


class TestListVersions(_Base):
    """``list_versions`` returns every row in the family newest-first
    and 404s when the seed id is in another realm."""

    async def test_list_versions_returns_family_newest_first(self):
        # Build v1 → publish → edit → v2 DRAFT inside realm-a.
        created = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="combo",
                type=StrategyDefinitionType.DSL_FULL,
                astJson={"type": "program", "rules": []},
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        await self.service.publish(id=created.id, realmId="realm-a")
        # Update on PUBLISHED forks a new draft at v2.
        await self.service.update(
            id=created.id,
            payload=StrategyDefinitionUpdate(description="v2"),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        versions = await self.service.list_versions(id=created.id, realmId="realm-a")
        self.assertEqual([v.version for v in versions], [2, 1])
        # Status assertions catch the publish/archive bookkeeping.
        self.assertEqual(versions[0].status, "DRAFT")
        self.assertEqual(versions[1].status, "PUBLISHED")

    async def test_list_versions_404s_on_unknown_id(self):
        with self.assertRaises(NotFoundError):
            await self.service.list_versions(id="does-not-exist", realmId="realm-a")

    async def test_list_versions_is_tenant_scoped(self):
        created = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="iso", type=StrategyDefinitionType.DSL_FULL
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        # realm-b probing realm-a's id must 404, not leak.
        with self.assertRaises(NotFoundError):
            await self.service.list_versions(id=created.id, realmId="realm-b")


class TestRollback(unittest.IsolatedAsyncioTestCase):
    """Sprint 9 rollback flow: archive the current PUBLISHED row,
    promote the target version, and cascade Games.strategyId /
    Tasks.strategyId rewrites so consumers never reference an
    ARCHIVED row."""

    def setUp(self):
        self.repo = FakeStrategyDefinitionRepository()
        self.games = FakeAssignmentRepository()
        self.tasks = FakeAssignmentRepository()
        self.service = StrategyDefinitionService(
            strategy_definition_repository=self.repo,
            game_repository=self.games,
            task_repository=self.tasks,
        )

    async def _build_two_versions(self):
        """Create v1 → publish → edit → v2 → publish; return both ids."""
        v1 = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="happy",
                type=StrategyDefinitionType.DSL_FULL,
                astJson={"type": "program", "rules": []},
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        await self.service.publish(id=v1.id, realmId="realm-a")
        v2_draft = await self.service.update(
            id=v1.id,
            payload=StrategyDefinitionUpdate(description="v2 desc"),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )
        v2 = await self.service.publish(id=v2_draft.id, realmId="realm-a")
        return v1, v2

    async def test_happy_path_promotes_v1_and_archives_v2(self):
        v1, v2 = await self._build_two_versions()
        # Games/Tasks point at v2 (the currently published row).
        self.games.rows = [f"custom:{v2.id}", f"custom:{v2.id}"]
        self.tasks.rows = [f"custom:{v2.id}"]

        result = await self.service.rollback(
            id=v2.id, target_version=1, realmId="realm-a"
        )

        self.assertEqual(result.strategy.id, v1.id)
        self.assertEqual(result.strategy.status, "PUBLISHED")
        self.assertEqual(result.games_reassigned, 2)
        self.assertEqual(result.tasks_reassigned, 1)
        # v2 must be archived now.
        v2_after = await self.repo.get_for_realm(id=v2.id, realmId="realm-a")
        self.assertEqual(v2_after.status, "ARCHIVED")
        # All games/tasks now point at v1.
        self.assertEqual(
            self.games.rows,
            [f"custom:{v1.id}", f"custom:{v1.id}"],
        )
        self.assertEqual(self.tasks.rows, [f"custom:{v1.id}"])

    async def test_refuses_rolling_back_to_published_version(self):
        _, v2 = await self._build_two_versions()
        with self.assertRaises(ConflictError):
            await self.service.rollback(
                id=v2.id,
                target_version=v2.version,
                realmId="realm-a",
            )

    async def test_404_on_unknown_target_version(self):
        _, v2 = await self._build_two_versions()
        with self.assertRaises(NotFoundError):
            await self.service.rollback(id=v2.id, target_version=99, realmId="realm-a")

    async def test_404_on_cross_realm_seed_id(self):
        _, v2 = await self._build_two_versions()
        with self.assertRaises(NotFoundError):
            await self.service.rollback(id=v2.id, target_version=1, realmId="realm-b")

    async def test_rollback_can_be_initiated_from_a_draft_seed(self):
        """An admin browsing history may click on v1 (ARCHIVED) to
        rollback to it - current published is still v2 and must get
        archived + reassigned."""
        v1, v2 = await self._build_two_versions()
        # After publish(v2), v1 was archived. Click on v1 to rollback.
        self.games.rows = [f"custom:{v2.id}"]
        result = await self.service.rollback(
            id=v1.id, target_version=1, realmId="realm-a"
        )
        self.assertEqual(result.strategy.id, v1.id)
        self.assertEqual(self.games.rows, [f"custom:{v1.id}"])

    async def test_rollback_requires_assignment_repositories(self):
        """Without game/task repos wired the cascade would silently
        skip - refuse the operation up front."""
        bare_service = StrategyDefinitionService(
            strategy_definition_repository=self.repo,
        )
        _, v2 = await self._build_two_versions()
        with self.assertRaises(BadRequestError):
            await bare_service.rollback(id=v2.id, target_version=1, realmId="realm-a")


class TestSprint9LifecycleEndToEnd(unittest.IsolatedAsyncioTestCase):
    """End-to-end lifecycle test mirroring the Sprint 9 done-criteria
    from the roadmap (see plan ``Post-S9`` verification section):

      1. Create + publish v1.
      2. Assign a Game and a Task to ``custom:<v1.id>``.
      3. Edit → forks v2 DRAFT. v1 still PUBLISHED → Games/Tasks still
         execute v1.
      4. Publish v2 → v1 ARCHIVED. Game/Task strategyIds still point at
         v1 (assignments don't cascade on publish).
      5. Reassign Game/Task to ``custom:<v2.id>``.
      6. Rollback to v1 → v2 ARCHIVED, v1 re-PUBLISHED, Game/Task
         strategyIds rewritten back to ``custom:<v1.id>``.

    Driven through the service against the same in-memory fakes used by
    the focused tests above so it stays a unit test rather than a real
    DB integration test (which would require migrations + Postgres
    and isn't worth the cost for the lifecycle assertion). The plan
    explicitly calls this scenario out as the sprint's acceptance
    criterion."""

    def setUp(self):
        self.repo = FakeStrategyDefinitionRepository()
        self.games = FakeAssignmentRepository()
        self.tasks = FakeAssignmentRepository()
        self.service = StrategyDefinitionService(
            strategy_definition_repository=self.repo,
            game_repository=self.games,
            task_repository=self.tasks,
        )

    async def test_full_lifecycle_matches_roadmap_done_criteria(self):
        # Step 1: create + publish v1.
        v1 = await self.service.create(
            payload=StrategyDefinitionCreate(
                name="endgame",
                type=StrategyDefinitionType.DSL_FULL,
                astJson={"type": "program", "rules": []},
            ),
            realmId="realm-a",
            createdBy="admin",
            apiKey_used=None,
            oauth_user_id=None,
        )
        v1 = await self.service.publish(id=v1.id, realmId="realm-a")
        self.assertEqual(v1.status, "PUBLISHED")

        # Step 2: assign a Game + a Task to v1.
        self.games.rows = [f"custom:{v1.id}"]
        self.tasks.rows = [f"custom:{v1.id}"]

        # Step 3: edit → fork v2 DRAFT.
        v2_draft = await self.service.update(
            id=v1.id,
            payload=StrategyDefinitionUpdate(
                description="new behaviour",
                astJson={"type": "program", "rules": []},
            ),
            realmId="realm-a",
            createdBy="admin",
            apiKey_used=None,
            oauth_user_id=None,
        )
        self.assertEqual(v2_draft.version, 2)
        self.assertEqual(v2_draft.status, "DRAFT")
        # v1 is still PUBLISHED and the Game/Task still execute it.
        v1_after_edit = await self.repo.get_for_realm(
            id=v1.id,
            realmId="realm-a",
        )
        self.assertEqual(v1_after_edit.status, "PUBLISHED")
        self.assertEqual(self.games.rows, [f"custom:{v1.id}"])

        # Step 4: publish v2 → v1 ARCHIVED. Assignments NOT cascaded on
        # publish (only rollback cascades) so the Game/Task still point
        # at the now-archived v1.
        v2 = await self.service.publish(id=v2_draft.id, realmId="realm-a")
        self.assertEqual(v2.status, "PUBLISHED")
        v1_after_publish = await self.repo.get_for_realm(
            id=v1.id,
            realmId="realm-a",
        )
        self.assertEqual(v1_after_publish.status, "ARCHIVED")
        self.assertEqual(self.games.rows, [f"custom:{v1.id}"])
        self.assertEqual(self.tasks.rows, [f"custom:{v1.id}"])

        # Step 5: manual reassignment of Game/Task to v2 (the
        # assignments admin view's PATCH path).
        self.games.rows = [f"custom:{v2.id}"]
        self.tasks.rows = [f"custom:{v2.id}"]

        # Step 6: rollback to v1 → v2 ARCHIVED, v1 re-PUBLISHED, all
        # assignments rewritten back to v1.
        result = await self.service.rollback(
            id=v2.id,
            target_version=1,
            realmId="realm-a",
        )
        self.assertEqual(result.strategy.id, v1.id)
        self.assertEqual(result.strategy.status, "PUBLISHED")
        self.assertEqual(result.games_reassigned, 1)
        self.assertEqual(result.tasks_reassigned, 1)
        v2_after = await self.repo.get_for_realm(
            id=v2.id,
            realmId="realm-a",
        )
        self.assertEqual(v2_after.status, "ARCHIVED")
        # The roadmap's done-criteria: Game.strategyId ends up pointing
        # at v1 after rollback. Same for Task.
        self.assertEqual(self.games.rows, [f"custom:{v1.id}"])
        self.assertEqual(self.tasks.rows, [f"custom:{v1.id}"])


class FakeUsageGameRepository:
    """
    Richer stand-in than :class:`FakeAssignmentRepository` for the usage
    lookup: rows expose the columns ``get_usage`` reads (id /
    externalGameId / platform) and the helper resolves external ids by id.
    """

    def __init__(self, games: Optional[List[SimpleNamespace]] = None):
        self.games: List[SimpleNamespace] = list(games or [])

    async def list_by_strategy_id(self, strategy_id: str):
        return [g for g in self.games if g.strategyId == strategy_id]

    async def list_external_ids(self, ids) -> Dict:
        wanted = {i for i in ids if i is not None}
        return {g.id: g.externalGameId for g in self.games if g.id in wanted}


class FakeUsageTaskRepository:
    def __init__(self, tasks: Optional[List[SimpleNamespace]] = None):
        self.tasks: List[SimpleNamespace] = list(tasks or [])

    async def list_by_strategy_id(self, strategy_id: str):
        return [t for t in self.tasks if t.strategyId == strategy_id]


class TestGetUsage(unittest.IsolatedAsyncioTestCase):
    """Sprint 6 reverse lookup: which games/tasks run this exact strategy
    version, with counts, for the blast-radius preview + bulk reassign."""

    def setUp(self):
        self.repo = FakeStrategyDefinitionRepository()
        self.games = FakeUsageGameRepository()
        self.tasks = FakeUsageTaskRepository()
        self.service = StrategyDefinitionService(
            strategy_definition_repository=self.repo,
            game_repository=self.games,
            task_repository=self.tasks,
        )

    async def _create(self, *, realm="realm-a", name="usage-strat"):
        return await self.service.create(
            payload=StrategyDefinitionCreate(
                name=name,
                type=StrategyDefinitionType.DSL_FULL,
                astJson={"type": "program", "rules": []},
            ),
            realmId=realm,
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

    async def test_lists_consumers_with_counts_and_parent_labels(self):
        strat = await self._create()
        assignable = f"custom:{strat.id}"
        game_a = SimpleNamespace(
            id=uuid.uuid4(),
            externalGameId="game-a",
            platform="web",
            strategyId=assignable,
        )
        game_other = SimpleNamespace(
            id=uuid.uuid4(),
            externalGameId="game-other",
            platform="web",
            strategyId="default",
        )
        self.games.games = [game_a, game_other]
        # A task overriding its parent game's default onto our strategy.
        self.tasks.tasks = [
            SimpleNamespace(
                id=uuid.uuid4(),
                externalTaskId="task-1",
                gameId=game_a.id,
                strategyId=assignable,
            ),
            SimpleNamespace(
                id=uuid.uuid4(),
                externalTaskId="task-other",
                gameId=game_other.id,
                strategyId="default",
            ),
        ]

        usage = await self.service.get_usage(id=strat.id, realmId="realm-a")

        # Only the consumers of THIS strategy are reported.
        self.assertEqual(usage.strategyId, assignable)
        self.assertEqual(usage.gameCount, 1)
        self.assertEqual(usage.taskCount, 1)
        self.assertEqual(usage.games[0].externalGameId, "game-a")
        self.assertEqual(usage.tasks[0].externalTaskId, "task-1")
        # Parent game external id is resolved for the task row.
        self.assertEqual(usage.tasks[0].externalGameId, "game-a")
        self.assertEqual(usage.version, strat.version)
        self.assertEqual(usage.status, strat.status)

    async def test_empty_when_no_consumers(self):
        strat = await self._create()
        usage = await self.service.get_usage(id=strat.id, realmId="realm-a")
        self.assertEqual(usage.gameCount, 0)
        self.assertEqual(usage.taskCount, 0)
        self.assertEqual(usage.games, [])
        self.assertEqual(usage.tasks, [])

    async def test_404_on_unknown_id(self):
        with self.assertRaises(NotFoundError):
            await self.service.get_usage(id="nope", realmId="realm-a")

    async def test_tenant_scoped(self):
        strat = await self._create()
        with self.assertRaises(NotFoundError):
            await self.service.get_usage(id=strat.id, realmId="realm-b")

    async def test_requires_assignment_repositories(self):
        bare = StrategyDefinitionService(
            strategy_definition_repository=self.repo,
        )
        strat = await self._create()
        with self.assertRaises(BadRequestError):
            await bare.get_usage(id=strat.id, realmId="realm-a")


if __name__ == "__main__":
    unittest.main()

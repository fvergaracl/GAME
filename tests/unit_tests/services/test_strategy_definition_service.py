"""
Unit tests for :class:`StrategyDefinitionService`.

These exercise the versioning / lifecycle rules in isolation using a
hand-rolled fake repository — the underlying repository is covered by
integration tests separately. The fake is intentionally tiny (just
enough state to drive the service's branches) so the test reads like a
spec for the service's behaviour.
"""

import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Dict, List, Optional

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    DuplicatedError,
    NotFoundError,
)
from app.model.strategy_definition import (
    StrategyDefinitionStatus,
    StrategyDefinitionType,
)
from app.schema.strategy_definition_schema import (
    StrategyDefinitionCreate,
    StrategyDefinitionUpdate,
)
from app.services.strategy_definition_service import (
    StrategyDefinitionService,
)


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
            [
                r
                for r in self._rows.values()
                if r.realmId == realmId and r.name == name
            ],
            key=lambda r: -r.version,
        )

    async def get_max_version(
        self, *, realmId: Optional[str], name: str
    ) -> int:
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
            astJson={"program": []},
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
        self.assertEqual(
            result.status, StrategyDefinitionStatus.DRAFT.value
        )
        self.assertEqual(result.realmId, "realm-a")
        self.assertEqual(result.type, StrategyDefinitionType.DSL_FULL.value)
        self.assertEqual(result.astJson, {"program": []})

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
            await self.service.get_strategy(
                id=created.id, realmId="realm-b"
            )

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
                astJson={"program": ["v1"]},
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
            payload=StrategyDefinitionUpdate(
                description="updated"
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        self.assertEqual(result.id, created.id)
        self.assertEqual(result.version, 1)
        self.assertEqual(result.description, "updated")
        self.assertEqual(
            result.status, StrategyDefinitionStatus.DRAFT.value
        )

    async def test_updating_published_forks_new_draft(self):
        published_id = await self._create_and_publish()

        forked = await self.service.update(
            id=published_id,
            payload=StrategyDefinitionUpdate(
                astJson={"program": ["v2"]}
            ),
            realmId="realm-a",
            createdBy=None,
            apiKey_used=None,
            oauth_user_id=None,
        )

        self.assertNotEqual(forked.id, published_id)
        self.assertEqual(forked.version, 2)
        self.assertEqual(
            forked.status, StrategyDefinitionStatus.DRAFT.value
        )
        self.assertEqual(forked.astJson, {"program": ["v2"]})

        # Published row is untouched.
        original = await self.service.get_strategy(
            id=published_id, realmId="realm-a"
        )
        self.assertEqual(
            original.status, StrategyDefinitionStatus.PUBLISHED.value
        )
        self.assertEqual(original.astJson, {"program": ["v1"]})

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
                payload=StrategyDefinitionUpdate(
                    description="too late"
                ),
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
        # Publish v2 — should archive v1.
        await self.service.publish(id=v2.id, realmId="realm-a")

        archived_v1 = await self.service.get_strategy(
            id=v1.id, realmId="realm-a"
        )
        live_v2 = await self.service.get_strategy(
            id=v2.id, realmId="realm-a"
        )
        self.assertEqual(
            archived_v1.status, StrategyDefinitionStatus.ARCHIVED.value
        )
        self.assertEqual(
            live_v2.status, StrategyDefinitionStatus.PUBLISHED.value
        )

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
        first = await self.service.publish(
            id=created.id, realmId="realm-a"
        )
        again = await self.service.publish(
            id=created.id, realmId="realm-a"
        )
        self.assertEqual(first.id, again.id)
        self.assertEqual(
            again.status, StrategyDefinitionStatus.PUBLISHED.value
        )

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
            await self.service.publish(
                id=created.id, realmId="realm-a"
            )


if __name__ == "__main__":
    unittest.main()

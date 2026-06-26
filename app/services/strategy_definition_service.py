"""
Service for the persistent strategy model.

Implements the versioning rules for the persistent strategy model:

* Creating uses ``version=1`` and ``status=DRAFT``.
* Editing a draft mutates the row in place.
* Editing a published row forks ``version + 1`` as a new draft instead
  of mutating the published copy.
* Publishing a draft transitions it to ``PUBLISHED`` and archives any
  sibling that was previously published, so a ``(realmId, name)``
  family only ever has at most one live row.
* Archiving moves a row out of the active set without deleting history.

Tenancy is enforced at this layer: every read/write takes ``realmId``
and we never accept it from the caller body - the endpoint resolves it
from the auth context and passes it in.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    DuplicatedError,
    NotFoundError,
)
from app.engine.dsl_validator import validate_ast
from app.model.strategy_definition import (
    StrategyDefinition,
    StrategyDefinitionStatus,
    StrategyDefinitionType,
)
from app.repository.strategy_definition_repository import StrategyDefinitionRepository
from app.schema.strategy_definition_schema import (
    StrategyDefinitionCreate,
    StrategyDefinitionPersist,
    StrategyDefinitionRead,
    StrategyDefinitionUpdate,
    StrategyUsageGame,
    StrategyUsageRead,
    StrategyUsageTask,
)
from app.services.base_service import BaseService

# Kept in sync with ``CUSTOM_STRATEGY_PREFIX`` in
# ``app/services/strategy_service.py``. We inline the literal here
# instead of importing it because ``StrategyService`` already imports
# this module - pulling the constant back the other way would create a
# circular module dependency (same reason ``_validate_payload`` doesn't
# resolve parent strategies; see comment below).
_CUSTOM_STRATEGY_PREFIX = "custom:"


@dataclass(frozen=True)
class RollbackResult:
    """Outcome of a rollback operation, returned by the service so the
    endpoint can include cascade counts in the audit log without re-hitting
    the DB."""

    strategy: StrategyDefinitionRead
    games_reassigned: int
    tasks_reassigned: int


class StrategyDefinitionService(BaseService):
    """
    CRUD + lifecycle operations for custom strategies.
    """

    def __init__(
        self,
        strategy_definition_repository: StrategyDefinitionRepository,
        game_repository=None,
        task_repository=None,
    ) -> None:
        """
        ``game_repository`` and ``task_repository`` are optional so legacy
        call sites that only need CRUD/lifecycle (most tests, the
        simulation service) keep working without a wider DI graph. The
        The rollback flow requires both - when missing,
        :meth:`rollback` raises a precise error rather than silently
        leaving cascade UPDATEs undone.
        """
        self.strategy_definition_repository = strategy_definition_repository
        self.game_repository = game_repository
        self.task_repository = task_repository
        super().__init__(strategy_definition_repository)

    @staticmethod
    def _to_read(row: StrategyDefinition) -> StrategyDefinitionRead:
        """
        Map a ``StrategyDefinition`` ORM row to its public read schema.

        Args:
            row (StrategyDefinition): The persisted definition row.

        Returns:
            StrategyDefinitionRead: The API-facing representation.
        """
        return StrategyDefinitionRead(
            id=str(row.id),
            realmId=row.realmId,
            name=row.name,
            description=row.description,
            type=row.type,
            parentStrategyId=row.parentStrategyId,
            astJson=row.astJson,
            blocklyXml=row.blocklyXml,
            version=row.version,
            status=row.status,
            createdBy=row.createdBy,
            created_at=row.created_at,
            updated_at=row.updated_at,
            publishedAt=row.publishedAt,
            experimentTag=row.experimentTag,
        )

    @staticmethod
    def _validate_payload(type_value: str, parentStrategyId: Optional[str]) -> None:
        """
        DSL_EXTEND must carry a parent; DSL_FULL must not. We don't yet
        validate that ``parentStrategyId`` resolves to a real registry
        entry because the registry is loaded lazily and importing it
        here would create a circular dependency - that check lives in
        the endpoint via :class:`StrategyService`.
        """
        if type_value == StrategyDefinitionType.DSL_EXTEND.value:
            if not parentStrategyId:
                raise BadRequestError(
                    detail="DSL_EXTEND strategies require parentStrategyId."
                )
        else:
            if parentStrategyId:
                raise BadRequestError(
                    detail=(
                        f"parentStrategyId is only valid when type="
                        f"{StrategyDefinitionType.DSL_EXTEND.value}."
                    )
                )

    async def name_exists(
        self,
        *,
        realmId: Optional[str],
        name: str,
    ) -> bool:
        """Whether any version of ``(realmId, name)`` already exists.

        Used by the import endpoint to decide whether the
        incoming bundle needs an auto-rename to avoid colliding with
        the ``UNIQUE(realmId, name, version)`` constraint.
        """
        max_version = await self.strategy_definition_repository.get_max_version(
            realmId=realmId, name=name
        )
        return max_version > 0

    async def list_strategies(
        self,
        *,
        realmId: Optional[str],
        status: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> List[StrategyDefinitionRead]:
        """
        List strategy definitions for a realm, optionally filtered.

        Args:
            realmId (Optional[str]): Realm/tenant to scope to.
            status (Optional[str]): Optional lifecycle-status filter.
            type (Optional[str]): Optional strategy-type filter.
            limit (int): Maximum rows to return.

        Returns:
            List[StrategyDefinitionRead]: The matching definitions.
        """
        rows = await self.strategy_definition_repository.list_for_realm(
            realmId=realmId, status=status, type=type, limit=limit
        )
        return [self._to_read(r) for r in rows]

    async def get_strategy(
        self,
        *,
        id: str,
        realmId: Optional[str],
    ) -> StrategyDefinitionRead:
        """
        Fetch one strategy definition scoped to a realm.

        Args:
            id (str): Strategy definition identifier.
            realmId (Optional[str]): Realm/tenant the strategy must belong to.

        Returns:
            StrategyDefinitionRead: The matching definition.

        Raises:
            NotFoundError: If no matching strategy exists in the realm.
        """
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(detail=f"Custom strategy not found: {id}")
        return self._to_read(row)

    async def create(
        self,
        *,
        payload: StrategyDefinitionCreate,
        realmId: Optional[str],
        createdBy: Optional[str],
        apiKey_used: Optional[str],
        oauth_user_id: Optional[str],
    ) -> StrategyDefinitionRead:
        """
        Create a new strategy-definition draft.

        Validates the type/parent combination and any provided AST, rejects a
        name that already exists in the realm, and persists the draft as
        version 1.

        Args:
            payload (StrategyDefinitionCreate): The strategy to create.
            realmId (Optional[str]): Realm/tenant that will own it.
            createdBy (Optional[str]): Identity recorded as the author.
            apiKey_used (Optional[str]): API key used for the request, if any.
            oauth_user_id (Optional[str]): OAuth subject, if any.

        Returns:
            StrategyDefinitionRead: The newly created draft.

        Raises:
            BadRequestError: If the type/parent combination is invalid.
            DuplicatedError: If a strategy with the same name already exists.
        """
        type_value = payload.type.value
        self._validate_payload(type_value, payload.parentStrategyId)
        if payload.astJson is not None:
            validate_ast(payload.astJson)

        existing_max = await self.strategy_definition_repository.get_max_version(
            realmId=realmId, name=payload.name
        )
        if existing_max > 0:
            raise DuplicatedError(
                detail=(
                    f"A strategy named '{payload.name}' already exists in "
                    "this realm. Edit the existing one to create a new "
                    "version."
                )
            )

        persist = StrategyDefinitionPersist(
            realmId=realmId,
            name=payload.name,
            description=payload.description,
            type=type_value,
            parentStrategyId=payload.parentStrategyId,
            astJson=payload.astJson,
            blocklyXml=payload.blocklyXml,
            version=1,
            status=StrategyDefinitionStatus.DRAFT.value,
            createdBy=createdBy,
            experimentTag=payload.experimentTag,
            apiKey_used=apiKey_used,
            oauth_user_id=oauth_user_id,
        )
        row = await self.strategy_definition_repository.create(persist)
        return self._to_read(row)

    async def update(
        self,
        *,
        id: str,
        payload: StrategyDefinitionUpdate,
        realmId: Optional[str],
        createdBy: Optional[str],
        apiKey_used: Optional[str],
        oauth_user_id: Optional[str],
    ) -> StrategyDefinitionRead:
        """
        Apply an update.

        * On a DRAFT row: patch in place and return the same id.
        * On a PUBLISHED row: fork a new DRAFT at ``version + 1`` with
          the patched fields applied, leaving the published row
          untouched so it keeps running until an explicit publish.
        * On an ARCHIVED row: refuse - archived strategies are
          immutable.
        """
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(detail=f"Custom strategy not found: {id}")

        if row.status == StrategyDefinitionStatus.ARCHIVED.value:
            raise ConflictError(
                detail=(
                    "Archived strategies cannot be edited. Clone the "
                    "definition into a new strategy if you need to "
                    "iterate on it."
                )
            )

        merged = {
            "name": payload.name if payload.name is not None else row.name,
            "description": (
                payload.description
                if payload.description is not None
                else row.description
            ),
            "type": (payload.type.value if payload.type is not None else row.type),
            "parentStrategyId": (
                payload.parentStrategyId
                if payload.parentStrategyId is not None
                else row.parentStrategyId
            ),
            "astJson": (
                payload.astJson if payload.astJson is not None else row.astJson
            ),
            "blocklyXml": (
                payload.blocklyXml if payload.blocklyXml is not None else row.blocklyXml
            ),
            "experimentTag": (
                payload.experimentTag
                if payload.experimentTag is not None
                else row.experimentTag
            ),
        }
        self._validate_payload(merged["type"], merged["parentStrategyId"])
        if merged["astJson"] is not None:
            validate_ast(merged["astJson"])

        if row.status == StrategyDefinitionStatus.DRAFT.value:
            patch = StrategyDefinitionUpdate(
                name=merged["name"],
                description=merged["description"],
                type=merged["type"],
                parentStrategyId=merged["parentStrategyId"],
                astJson=merged["astJson"],
                blocklyXml=merged["blocklyXml"],
                experimentTag=merged["experimentTag"],
            )
            updated = await self.strategy_definition_repository.update(id, patch)
            return self._to_read(updated)

        # PUBLISHED → fork a new draft with the merged contents.
        next_version = (
            await self.strategy_definition_repository.get_max_version(
                realmId=realmId, name=row.name
            )
        ) + 1
        persist = StrategyDefinitionPersist(
            realmId=realmId,
            name=merged["name"],
            description=merged["description"],
            type=merged["type"],
            parentStrategyId=merged["parentStrategyId"],
            astJson=merged["astJson"],
            blocklyXml=merged["blocklyXml"],
            version=next_version,
            status=StrategyDefinitionStatus.DRAFT.value,
            createdBy=createdBy,
            experimentTag=merged["experimentTag"],
            apiKey_used=apiKey_used,
            oauth_user_id=oauth_user_id,
        )
        new_row = await self.strategy_definition_repository.create(persist)
        return self._to_read(new_row)

    async def publish(
        self,
        *,
        id: str,
        realmId: Optional[str],
    ) -> StrategyDefinitionRead:
        """
        Publish a draft strategy, archiving any previously-published sibling.

        Idempotent: re-publishing an already-published row is a no-op. If
        another version of the same name is published, it is archived first so
        only one published version exists per name.

        Args:
            id (str): Strategy definition identifier.
            realmId (Optional[str]): Realm/tenant the strategy must belong to.

        Returns:
            StrategyDefinitionRead: The published strategy.

        Raises:
            NotFoundError: If no matching strategy exists in the realm.
            ConflictError: If the strategy is archived.
        """
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(detail=f"Custom strategy not found: {id}")
        if row.status == StrategyDefinitionStatus.ARCHIVED.value:
            raise ConflictError(detail="Cannot publish an archived strategy.")
        if row.status == StrategyDefinitionStatus.PUBLISHED.value:
            # Idempotent: re-publishing the same row is a no-op.
            return self._to_read(row)

        sibling = await self.strategy_definition_repository.get_published(
            realmId=realmId, name=row.name
        )
        if sibling is not None and str(sibling.id) != str(row.id):
            await self.strategy_definition_repository.set_status(
                id=str(sibling.id),
                status=StrategyDefinitionStatus.ARCHIVED.value,
            )

        await self.strategy_definition_repository.set_status(
            id=str(row.id),
            status=StrategyDefinitionStatus.PUBLISHED.value,
            publishedAt=datetime.now(timezone.utc),
        )
        return await self.get_strategy(id=id, realmId=realmId)

    async def archive(
        self,
        *,
        id: str,
        realmId: Optional[str],
    ) -> StrategyDefinitionRead:
        """
        Archive a strategy so it can no longer be published or assigned.

        Idempotent: archiving an already-archived row returns it unchanged.

        Args:
            id (str): Strategy definition identifier.
            realmId (Optional[str]): Realm/tenant the strategy must belong to.

        Returns:
            StrategyDefinitionRead: The archived strategy.

        Raises:
            NotFoundError: If no matching strategy exists in the realm.
        """
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(detail=f"Custom strategy not found: {id}")
        if row.status == StrategyDefinitionStatus.ARCHIVED.value:
            return self._to_read(row)

        await self.strategy_definition_repository.set_status(
            id=str(row.id),
            status=StrategyDefinitionStatus.ARCHIVED.value,
        )
        return await self.get_strategy(id=id, realmId=realmId)

    async def list_versions(
        self,
        *,
        id: str,
        realmId: Optional[str],
    ) -> List[StrategyDefinitionRead]:
        """
        Return every version in the family that contains ``id``, newest
        first. The caller passes a single id (typically the current
        published version) and we resolve the family name from it so the
        endpoint contract stays "one id in, full history out".

        Tenant-scoped: ``get_for_realm`` 404s when the row belongs to
        another realm, so cross-tenant probing returns nothing.
        """
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(detail=f"Custom strategy not found: {id}")
        rows = await self.strategy_definition_repository.list_versions(
            realmId=realmId, name=row.name
        )
        return [self._to_read(r) for r in rows]

    async def get_usage(
        self,
        *,
        id: str,
        realmId: Optional[str],
    ) -> StrategyUsageRead:
        """
        Reverse lookup: which games/tasks are assigned to this exact
        strategy version.

        Consumers store the assignable id ``custom:<uuid>``, so usage is
        an exact match on that string - the same value the rollback
        cascade rewrites. We report per-version (not per-family) because
        each published version is a distinct uuid that games point at
        individually; that matches what an admin needs to see before
        reassigning, archiving or rolling back *this* version.

        Tenant-scoped via ``get_for_realm``: a cross-realm id 404s.
        No cross-tenant leak through the usage lists either - a game can
        only be assigned a strategy validated to live in its own realm,
        so every consumer of ``custom:<uuid>`` shares the strategy's
        realm.
        """
        if self.game_repository is None or self.task_repository is None:
            raise BadRequestError(
                detail=(
                    "Usage lookup requires game/task repositories wired "
                    "into StrategyDefinitionService."
                )
            )

        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(detail=f"Custom strategy not found: {id}")

        assignable_id = f"{_CUSTOM_STRATEGY_PREFIX}{row.id}"
        game_rows = await self.game_repository.list_by_strategy_id(assignable_id)
        task_rows = await self.task_repository.list_by_strategy_id(assignable_id)

        # Resolve each task's parent game external id in one batched query
        # so the UI can show "task X of game Y" rather than a raw UUID.
        parent_ids = {t.gameId for t in task_rows if t.gameId is not None}
        external_by_game = await self.game_repository.list_external_ids(parent_ids)

        games = [
            StrategyUsageGame(
                gameId=str(g.id),
                externalGameId=g.externalGameId,
                platform=g.platform,
            )
            for g in game_rows
        ]
        tasks = [
            StrategyUsageTask(
                taskId=str(t.id),
                externalTaskId=t.externalTaskId,
                gameId=str(t.gameId) if t.gameId is not None else None,
                externalGameId=external_by_game.get(t.gameId),
            )
            for t in task_rows
        ]

        return StrategyUsageRead(
            strategyId=assignable_id,
            name=row.name,
            version=row.version,
            status=row.status,
            gameCount=len(games),
            taskCount=len(tasks),
            games=games,
            tasks=tasks,
        )

    async def rollback(
        self,
        *,
        id: str,
        target_version: int,
        realmId: Optional[str],
    ) -> RollbackResult:
        """
        Promote ``target_version`` back to PUBLISHED in the family that
        contains ``id``, archive whichever version is currently published,
        and rewrite every ``Games.strategyId`` / ``Tasks.strategyId``
        pointing at the displaced row so no consumer is left referencing
        an ARCHIVED row.

        ``id`` doesn't have to be PUBLISHED: an admin may initiate rollback
        from any version of the family (e.g. browsing the version history
        UI). We always treat the family's *current* PUBLISHED row as the
        one to archive + reassign, regardless of which id was clicked.

        Errors:
          * 404 if ``id`` doesn't resolve (or is in another realm).
          * 404 if ``target_version`` isn't a version of that family.
          * 409 if the requested target is the row that's already PUBLISHED
            - rolling back to the current state would be a no-op that
            falsely advertises a status change in the audit log.
        """
        if self.game_repository is None or self.task_repository is None:
            # Defensive: rollback writes to Games/Tasks. If those weren't
            # wired we'd silently leave the cascade undone - much worse
            # than refusing the operation up front.
            raise BadRequestError(
                detail=(
                    "Rollback requires game/task repositories wired into "
                    "StrategyDefinitionService."
                )
            )

        current = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if current is None:
            raise NotFoundError(detail=f"Custom strategy not found: {id}")

        target = await self.strategy_definition_repository.get_version(
            realmId=realmId,
            name=current.name,
            version=target_version,
        )
        if target is None:
            raise NotFoundError(
                detail=(
                    f"Version {target_version} not found for strategy "
                    f"'{current.name}'."
                )
            )

        displaced = await self.strategy_definition_repository.get_published(
            realmId=realmId, name=current.name
        )

        if displaced is not None and str(displaced.id) == str(target.id):
            # Target is already the live PUBLISHED row - rollback would be
            # a no-op and would obscure intent in the audit trail.
            raise ConflictError(
                detail=(
                    f"Version {target_version} is already the published "
                    f"version of '{current.name}'."
                )
            )

        # Order matters: archive the displaced row first, then promote
        # the target, then run the cascade. If a failure interrupts the
        # sequence the worst observable state is "0 PUBLISHED in family"
        # for a few ms - preferable to leaving two PUBLISHED rows.
        if displaced is not None:
            await self.strategy_definition_repository.set_status(
                id=str(displaced.id),
                status=StrategyDefinitionStatus.ARCHIVED.value,
            )
        await self.strategy_definition_repository.set_status(
            id=str(target.id),
            status=StrategyDefinitionStatus.PUBLISHED.value,
            publishedAt=datetime.now(timezone.utc),
        )

        games_reassigned = 0
        tasks_reassigned = 0
        if displaced is not None:
            old_strategy_id = f"{_CUSTOM_STRATEGY_PREFIX}{displaced.id}"
            new_strategy_id = f"{_CUSTOM_STRATEGY_PREFIX}{target.id}"
            games_reassigned = await self.game_repository.bulk_update_strategy_id(
                old_strategy_id=old_strategy_id,
                new_strategy_id=new_strategy_id,
            )
            tasks_reassigned = await self.task_repository.bulk_update_strategy_id(
                old_strategy_id=old_strategy_id,
                new_strategy_id=new_strategy_id,
            )

        promoted = await self.get_strategy(id=str(target.id), realmId=realmId)
        return RollbackResult(
            strategy=promoted,
            games_reassigned=games_reassigned,
            tasks_reassigned=tasks_reassigned,
        )

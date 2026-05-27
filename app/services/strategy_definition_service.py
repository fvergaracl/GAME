"""
Service for the persistent strategy model.

Implements the versioning rules called out in the Sprint 3 plan:

* Creating uses ``version=1`` and ``status=DRAFT``.
* Editing a draft mutates the row in place.
* Editing a published row forks ``version + 1`` as a new draft instead
  of mutating the published copy.
* Publishing a draft transitions it to ``PUBLISHED`` and archives any
  sibling that was previously published, so a ``(realmId, name)``
  family only ever has at most one live row.
* Archiving moves a row out of the active set without deleting history.

Tenancy is enforced at this layer: every read/write takes ``realmId``
and we never accept it from the caller body — the endpoint resolves it
from the auth context and passes it in.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    DuplicatedError,
    NotFoundError,
)
from app.model.strategy_definition import (
    StrategyDefinition,
    StrategyDefinitionStatus,
    StrategyDefinitionType,
)
from app.repository.strategy_definition_repository import (
    StrategyDefinitionRepository,
)
from app.schema.strategy_definition_schema import (
    StrategyDefinitionCreate,
    StrategyDefinitionPersist,
    StrategyDefinitionRead,
    StrategyDefinitionUpdate,
)
from app.services.base_service import BaseService


class StrategyDefinitionService(BaseService):
    """
    CRUD + lifecycle operations for custom strategies.
    """

    def __init__(
        self,
        strategy_definition_repository: StrategyDefinitionRepository,
    ) -> None:
        self.strategy_definition_repository = strategy_definition_repository
        super().__init__(strategy_definition_repository)

    @staticmethod
    def _to_read(row: StrategyDefinition) -> StrategyDefinitionRead:
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
    def _validate_payload(
        type_value: str, parentStrategyId: Optional[str]
    ) -> None:
        """
        DSL_EXTEND must carry a parent; DSL_FULL must not. We don't yet
        validate that ``parentStrategyId`` resolves to a real registry
        entry because the registry is loaded lazily and importing it
        here would create a circular dependency — that check lives in
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

    async def list_strategies(
        self,
        *,
        realmId: Optional[str],
        status: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> List[StrategyDefinitionRead]:
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
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(
                detail=f"Custom strategy not found: {id}"
            )
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
        type_value = payload.type.value
        self._validate_payload(type_value, payload.parentStrategyId)

        existing_max = (
            await self.strategy_definition_repository.get_max_version(
                realmId=realmId, name=payload.name
            )
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
        * On an ARCHIVED row: refuse — archived strategies are
          immutable.
        """
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(
                detail=f"Custom strategy not found: {id}"
            )

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
            "type": (
                payload.type.value if payload.type is not None else row.type
            ),
            "parentStrategyId": (
                payload.parentStrategyId
                if payload.parentStrategyId is not None
                else row.parentStrategyId
            ),
            "astJson": (
                payload.astJson
                if payload.astJson is not None
                else row.astJson
            ),
            "blocklyXml": (
                payload.blocklyXml
                if payload.blocklyXml is not None
                else row.blocklyXml
            ),
            "experimentTag": (
                payload.experimentTag
                if payload.experimentTag is not None
                else row.experimentTag
            ),
        }
        self._validate_payload(merged["type"], merged["parentStrategyId"])

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
            updated = await self.strategy_definition_repository.update(
                id, patch
            )
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
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(
                detail=f"Custom strategy not found: {id}"
            )
        if row.status == StrategyDefinitionStatus.ARCHIVED.value:
            raise ConflictError(
                detail="Cannot publish an archived strategy."
            )
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
        row = await self.strategy_definition_repository.get_for_realm(
            id=id, realmId=realmId
        )
        if row is None:
            raise NotFoundError(
                detail=f"Custom strategy not found: {id}"
            )
        if row.status == StrategyDefinitionStatus.ARCHIVED.value:
            return self._to_read(row)

        await self.strategy_definition_repository.set_status(
            id=str(row.id),
            status=StrategyDefinitionStatus.ARCHIVED.value,
        )
        return await self.get_strategy(id=id, realmId=realmId)



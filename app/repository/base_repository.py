from contextlib import AbstractAsyncContextManager
from typing import Callable, Optional

from sqlalchemy import and_
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import configs
from app.core.exceptions import DuplicatedError, NotFoundError
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class BaseRepository:
    """
    Async base repository providing common CRUD operations on top of
    SQLAlchemy 2.0's ``AsyncSession``.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model,
    ) -> None:
        self.session_factory = session_factory
        self.model = model

    async def read_by_options(self, schema, eager: bool = False):
        async with self.session_factory() as session:
            schema_as_dict = schema.model_dump(exclude_none=True)
            ordering = schema_as_dict.get("ordering", configs.ORDERING)
            order_query = (
                getattr(self.model, ordering[1:]).desc()
                if ordering.startswith("-")
                else getattr(self.model, ordering).asc()
            )
            page = schema_as_dict.get("page", configs.PAGE)
            page_size = schema_as_dict.get("page_size", configs.PAGE_SIZE)
            filter_options = dict_to_sqlalchemy_filter_options(
                self.model, schema.model_dump(exclude_none=True)
            )

            stmt = select(self.model)
            if eager:
                for eager_rel in getattr(self.model, "eagers", []):
                    stmt = stmt.options(joinedload(getattr(self.model, eager_rel)))
            stmt = stmt.filter(filter_options)
            count_stmt = select(func.count()).select_from(
                select(self.model).filter(filter_options).subquery()
            )
            stmt = stmt.order_by(order_query)
            if page_size != "all":
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt)
            items = result.unique().scalars().all()
            total_count = (await session.execute(count_stmt)).scalar_one()
            return {
                "items": items,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            }

    async def read_by_id(
        self,
        id,
        eager: bool = False,
        not_found_raise_exception: bool = True,
        not_found_message: str = "Not found id : {id}",
    ):
        async with self.session_factory() as session:
            stmt = select(self.model).filter(self.model.id == id)
            if eager:
                for eager_rel in getattr(self.model, "eagers", []):
                    stmt = stmt.options(joinedload(getattr(self.model, eager_rel)))
            result = (await session.execute(stmt)).unique().scalars().first()
            if not result and not_found_raise_exception:
                raise NotFoundError(detail=not_found_message.format(id=id))
            return result

    async def read_by_column(
        self,
        column: str,
        value,
        eager: bool = False,
        only_one: bool = True,
        not_found_raise_exception: bool = True,
        not_found_message: str = "Not found {column} : {value}",
    ):
        async with self.session_factory() as session:
            stmt = select(self.model).filter(getattr(self.model, column) == value)
            if eager:
                for eager_rel in getattr(self.model, "eagers", []):
                    stmt = stmt.options(joinedload(getattr(self.model, eager_rel)))
            executed = await session.execute(stmt)
            if only_one:
                result = executed.unique().scalars().first()
                if not result and not_found_raise_exception:
                    raise NotFoundError(
                        detail=not_found_message.format(column=column, value=value)
                    )
                return result
            return executed.unique().scalars().all()

    async def create(
        self,
        schema,
        session: Optional[AsyncSession] = None,
        auto_commit: bool = True,
    ):
        if session is None and not auto_commit:
            raise ValueError(
                "auto_commit=False requires an external session managed by the caller."
            )
        if session is None:
            async with self.session_factory() as managed_session:
                return await self.create(
                    schema,
                    session=managed_session,
                    auto_commit=auto_commit,
                )

        entity = self.model(**schema.model_dump())
        try:
            session.add(entity)
            if auto_commit:
                await session.commit()
            else:
                await session.flush()
            await session.refresh(entity)
        except IntegrityError as e:
            if auto_commit:
                await session.rollback()
            raise DuplicatedError(detail=str(e.orig))
        return entity

    async def update(self, id, schema):
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model)
                .where(self.model.id == id)
                .values(**schema.model_dump(exclude_none=True))
            )
            await session.commit()
            return await self.read_by_id(id)

    async def update_attr(self, id, column: str, value):
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model)
                .where(self.model.id == id)
                .values(**{column: value})
            )
            await session.commit()
            return await self.read_by_id(id)

    async def whole_update(self, id, schema):
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model)
                .where(self.model.id == id)
                .values(**schema.model_dump())
            )
            await session.commit()
            return await self.read_by_id(id)

    async def delete_by_id(self, id):
        async with self.session_factory() as session:
            stmt = select(self.model).filter(self.model.id == id)
            entity = (await session.execute(stmt)).scalars().first()
            if not entity:
                raise NotFoundError(detail=f"Not found id : {id}")
            await session.execute(sa_delete(self.model).where(self.model.id == id))
            await session.commit()

    async def read_by_columns(
        self,
        filters: dict,
        eager: bool = False,
        only_one: bool = True,
        not_found_raise_exception: bool = True,
    ):
        async with self.session_factory() as session:
            stmt = select(self.model)
            if eager:
                for eager_field in getattr(self.model, "eagers", []):
                    stmt = stmt.options(joinedload(getattr(self.model, eager_field)))
            conditions = [
                getattr(self.model, col) == val for col, val in filters.items()
            ]
            stmt = stmt.filter(and_(*conditions))
            executed = await session.execute(stmt)
            if only_one:
                result = executed.unique().scalars().first()
                if not result and not_found_raise_exception:
                    raise NotFoundError(detail=f"Not found for filters: {filters}")
                return result
            return executed.unique().scalars().all()

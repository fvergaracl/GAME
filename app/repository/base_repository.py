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
        """
        Run a filtered, ordered and paginated query from a search schema.

        Non-null fields on ``schema`` are turned into ``WHERE`` conditions;
        ``ordering``, ``page`` and ``page_size`` drive sorting and pagination
        (a ``page_size`` of ``"all"`` disables the limit). The total row count
        ignoring pagination is computed alongside the page.

        Args:
            schema: Search schema whose non-null fields become filters and
                which may carry ``ordering``/``page``/``page_size``.
            eager (bool): When ``True``, eagerly join the model's ``eagers``
                relationships.

        Returns:
            dict: ``{"items": [...], "search_options": {page, page_size,
            ordering, total_count}}``.
        """
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
        """
        Fetch a single row by primary key.

        Args:
            id: Primary-key value to look up.
            eager (bool): When ``True``, eagerly join the model's ``eagers``
                relationships.
            not_found_raise_exception (bool): Raise :class:`NotFoundError`
                when no row matches; when ``False`` return ``None`` instead.
            not_found_message (str): Format string for the not-found error
                (``{id}`` is substituted).

        Returns:
            The matching model instance, or ``None`` when missing and
            ``not_found_raise_exception`` is ``False``.

        Raises:
            NotFoundError: If no row matches and the flag is ``True``.
        """
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
        """
        Fetch rows whose ``column`` equals ``value``.

        Args:
            column (str): Name of the model attribute to filter on.
            value: Value the column must equal.
            eager (bool): When ``True``, eagerly join the model's ``eagers``
                relationships.
            only_one (bool): Return the first match when ``True``; otherwise
                return the full list of matches.
            not_found_raise_exception (bool): When ``only_one`` is ``True``,
                raise :class:`NotFoundError` if nothing matches.
            not_found_message (str): Format string for the not-found error
                (``{column}`` and ``{value}`` are substituted).

        Returns:
            A single instance (or ``None``) when ``only_one`` is ``True``,
            otherwise a list of matching instances.

        Raises:
            NotFoundError: If ``only_one`` and nothing matches and the flag is
                ``True``.
        """
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
        """
        Insert a new row built from ``schema``.

        Supports two modes: a self-managed session (``session=None``,
        ``auto_commit=True``) that opens, commits and closes its own session,
        or an externally-managed session passed by the caller so the insert
        can take part in a larger transaction (``auto_commit=False`` flushes
        instead of committing).

        Args:
            schema: Pydantic schema dumped into the model's constructor.
            session (Optional[AsyncSession]): Caller-managed session to reuse;
                a new one is opened when ``None``.
            auto_commit (bool): Commit immediately when ``True``; otherwise
                only flush (requires an external ``session``).

        Returns:
            The persisted (and refreshed) model instance.

        Raises:
            ValueError: If ``auto_commit=False`` is requested without an
                external session.
            DuplicatedError: If the insert violates a uniqueness constraint.
        """
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
        """
        Partially update a row, ignoring ``None`` fields on ``schema``.

        Args:
            id: Primary key of the row to update.
            schema: Pydantic schema; only its non-null fields are written.

        Returns:
            The refreshed model instance after the update.
        """
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model)
                .where(self.model.id == id)
                .values(**schema.model_dump(exclude_none=True))
            )
            await session.commit()
            return await self.read_by_id(id)

    async def update_attr(self, id, column: str, value):
        """
        Update a single column of a row.

        Args:
            id: Primary key of the row to update.
            column (str): Name of the column to set.
            value: New value for the column.

        Returns:
            The refreshed model instance after the update.
        """
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model)
                .where(self.model.id == id)
                .values(**{column: value})
            )
            await session.commit()
            return await self.read_by_id(id)

    async def whole_update(self, id, schema):
        """
        Fully replace a row's columns from ``schema`` (including ``None``).

        Unlike :meth:`update`, every field on ``schema`` is written, so this
        performs a complete overwrite rather than a partial patch.

        Args:
            id: Primary key of the row to update.
            schema: Pydantic schema dumped in full into the update.

        Returns:
            The refreshed model instance after the update.
        """
        async with self.session_factory() as session:
            await session.execute(
                sa_update(self.model)
                .where(self.model.id == id)
                .values(**schema.model_dump())
            )
            await session.commit()
            return await self.read_by_id(id)

    async def delete_by_id(self, id):
        """
        Delete a row by primary key.

        Args:
            id: Primary key of the row to delete.

        Raises:
            NotFoundError: If no row matches ``id``.
        """
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
        """
        Fetch rows matching several equality filters combined with ``AND``.

        Args:
            filters (dict): Mapping of column name to required value; all
                conditions must hold (``AND``).
            eager (bool): When ``True``, eagerly join the model's ``eagers``
                relationships.
            only_one (bool): Return the first match when ``True``; otherwise
                return all matches.
            not_found_raise_exception (bool): When ``only_one`` is ``True``,
                raise :class:`NotFoundError` if nothing matches.

        Returns:
            A single instance (or ``None``) when ``only_one`` is ``True``,
            otherwise a list of matching instances.

        Raises:
            NotFoundError: If ``only_one`` and nothing matches and the flag is
                ``True``.
        """
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

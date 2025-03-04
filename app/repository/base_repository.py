from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import configs
from app.core.exceptions import DuplicatedError, NotFoundError
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class BaseRepository:
    """
    Base repository providing common CRUD operations.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class.
    """

    def __init__(
        self, session_factory: Callable[..., AbstractContextManager[Session]], model
    ) -> None:
        """
        Initializes the BaseRepository with the provided session factory and
          model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class.
        """
        self.session_factory = session_factory
        self.model = model

    def read_by_options(self, schema, eager=False):
        """
        Reads records by specified options.

        Args:
            schema: The schema containing query options.
            eager (bool): Whether to use eager loading.

        Returns:
            dict: Query results and search options.
        """
        with self.session_factory() as session:
            schema_as_dict = schema.dict(exclude_none=True)
            ordering = schema_as_dict.get("ordering", configs.ORDERING)
            order_query = (
                getattr(self.model, ordering[1:]).desc()
                if ordering.startswith("-")
                else getattr(self.model, ordering).asc()
            )
            page = schema_as_dict.get("page", configs.PAGE)
            page_size = schema_as_dict.get("page_size", configs.PAGE_SIZE)
            filter_options = dict_to_sqlalchemy_filter_options(
                self.model, schema.dict(exclude_none=True)
            )
            query = session.query(self.model)
            if eager:
                for eager in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, eager)))
            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)
            if page_size == "all":
                query = query.all()
            else:
                query = query.limit(page_size).offset((page - 1) * page_size).all()
            total_count = filtered_query.count()
            return {
                "items": query,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            }

    def read_by_id(
        self,
        id: int,
        eager=False,
        not_found_raise_exception=True,
        not_found_message="Not found id : {id}",
    ):
        """
        Reads a record by its ID.

        Args:
            id (int): The record ID.
            eager (bool): Whether to use eager loading.
            not_found_raise_exception (bool): Whether to raise an exception if
              the record is not found.
            not_found_message (str): The message for the not found exception.

        Returns:
            object: The record if found, otherwise None or raises an exception.
        """
        with self.session_factory() as session:
            query = session.query(self.model)
            if eager:
                for eager in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, eager)))
            query = query.filter(self.model.id == id).first()
            if not query and not_found_raise_exception:
                raise NotFoundError(detail=not_found_message.format(id=id))
            if not not_found_raise_exception and not query:
                return None
            return query

    def read_by_column(
        self,
        column: str,
        value: str,
        eager=False,
        only_one=True,
        not_found_raise_exception=True,
        not_found_message="Not found {column} : {value}",
    ):
        """
        Reads records by a specified column and value.

        Args:
            column (str): The column name.
            value (str): The value to filter by.
            eager (bool): Whether to use eager loading.
            only_one (bool): Whether to return only one record.
            not_found_raise_exception (bool): Whether to raise an exception if
              the record is not found.
            not_found_message (str): The message for the not found exception.

        Returns:
            object or list: The record(s) if found, otherwise None or raises
              an exception.
        """
        with self.session_factory() as session:
            query = session.query(self.model)
            if eager:
                for eager in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, eager)))
            if only_one:
                query = query.filter(getattr(self.model, column) == value).first()
                if not query and not_found_raise_exception:
                    raise NotFoundError(
                        detail=not_found_message.format(column=column, value=value)
                    )
                return query
            query = query.filter(getattr(self.model, column) == value).all()
            return query

    async def create(self, schema):
        """
        Creates a new record.

        Args:
            schema: The schema containing the record data.

        Returns:
            object: The created record.
        """
        with self.session_factory() as session:
            query = self.model(**schema.dict())
            try:
                session.add(query)
                session.commit()
                session.refresh(query)
            except IntegrityError as e:
                raise DuplicatedError(detail=str(e.orig))
            return query

    def update(self, id: int, schema):
        """
        Updates a record by its ID.

        Args:
            id (int): The record ID.
            schema: The schema containing the updated data.

        Returns:
            object: The updated record.
        """
        with self.session_factory() as session:
            session.query(self.model).filter(self.model.id == id).update(
                schema.dict(exclude_none=True)
            )
            session.commit()
            return self.read_by_id(id)

    def update_attr(self, id: int, column: str, value):
        """
        Updates a specific attribute of a record by its ID.

        Args:
            id (int): The record ID.
            column (str): The column name.
            value: The new value of the attribute.

        Returns:
            object: The updated record.
        """
        with self.session_factory() as session:
            session.query(self.model).filter(self.model.id == id).update(
                {column: value}
            )
            session.commit()
            return self.read_by_id(id)

    def whole_update(self, id: int, schema):
        """
        Replaces a record entirely by its ID.

        Args:
            id (int): The record ID.
            schema: The schema containing the new data.

        Returns:
            object: The updated record.
        """
        with self.session_factory() as session:
            session.query(self.model).filter(self.model.id == id).update(schema.dict())
            session.commit()
            return self.read_by_id(id)

    def delete_by_id(self, id: int):
        """
        Deletes a record by its ID.

        Args:
            id (int): The record ID.

        Returns:
            None
        """
        with self.session_factory() as session:
            query = session.query(self.model).filter(self.model.id == id).first()
            if not query:
                raise NotFoundError(detail=f"Not found id : {id}")
            session.delete(query)
            session.commit()

    def read_by_columns(
        self, filters: dict, eager=False, only_one=True, not_found_raise_exception=True
    ):
        """
        Reads records based on multiple column filters.

        Args:
            filters (dict): Dictionary where keys are column names and values are filter values.
            eager (bool): Whether to use eager loading.
            only_one (bool): Whether to return only one record.
            not_found_raise_exception (bool): Whether to raise an exception if the record is not found.

        Returns:
            object or list: The record(s) if found, otherwise None or raises an exception.
        """
        with self.session_factory() as session:
            query = session.query(self.model)

            # Aplicar cargas ansiosas si están definidas en el modelo
            if eager:
                for eager_field in getattr(self.model, "eagers", []):
                    query = query.options(joinedload(getattr(self.model, eager_field)))

            # Construir el filtro dinámicamente
            filter_conditions = [
                getattr(self.model, col) == val for col, val in filters.items()
            ]
            query = query.filter(and_(*filter_conditions))

            # Retornar un solo resultado o una lista de resultados
            if only_one:
                result = query.first()
                if not result and not_found_raise_exception:
                    raise NotFoundError(detail=f"Not found for filters: {filters}")
                return result
            else:
                return query.all()

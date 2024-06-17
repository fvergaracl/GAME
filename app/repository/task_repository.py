from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session, joinedload

from app.core.config import configs
from app.core.exceptions import NotFoundError
from app.model.tasks import Tasks
from app.repository.base_repository import BaseRepository
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class TaskRepository(BaseRepository):
    """
    Repository class for tasks.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for tasks.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=Tasks,
    ) -> None:
        """
        Initializes the TaskRepository with the provided session factory and
          model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for tasks.
        """
        super().__init__(session_factory, model)

    def read_by_gameId(self, schema, eager=False):
        """
        Reads tasks by game ID based on the provided schema.

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

    def read_by_gameId_and_externalTaskId(self, gameId: int, externalTaskId: str):
        """
        Reads a task by game ID and external task ID.

        Args:
            gameId (int): The game ID.
            externalTaskId (str): The external task ID.

        Returns:
            object: The task if found, otherwise None.
        """
        with self.session_factory() as session:
            query = (
                session.query(self.model)
                .filter(
                    self.model.gameId == gameId,
                    self.model.externalTaskId == externalTaskId,
                )
                .first()
            )
            return query

    def get_points_and_users_by_taskId(self, taskId):
        """
        Retrieves points and users associated with a task ID.

        Args:
            taskId (int): The task ID.

        Returns:
            object: The task if found, otherwise raises NotFoundError.
        """
        with self.session_factory() as session:
            query = session.query(self.model).filter(self.model.id == taskId).first()
            if not query:
                raise NotFoundError(detail=f"Task not found by id : {taskId}")
            return query

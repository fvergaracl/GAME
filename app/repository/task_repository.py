from contextlib import AbstractContextManager
from typing import Callable
from app.core.config import configs
from sqlalchemy.orm import Session, joinedload
from app.model.tasks import Tasks
from app.repository.base_repository import BaseRepository
from app.util.query_builder import dict_to_sqlalchemy_filter_options


class TaskRepository(BaseRepository):

    def __init__(
        self,
        session_factory: Callable[
            ...,
            AbstractContextManager[Session]],
            model=Tasks) -> None:
        super().__init__(session_factory, model)

    def read_by_gameId(self, schema, eager=False):
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
                self.model, schema.dict(exclude_none=True))
            query = session.query(self.model)
            if eager:
                for eager in getattr(self.model, "eagers", []):
                    query = query.options(
                        joinedload(getattr(self.model, eager)))
            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)
            if page_size == "all":
                query = query.all()
            else:
                query = query.limit(page_size).offset(
                    (page - 1) * page_size).all()
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

    # gameId and externalTaskId
    def read_by_gameId_and_externalTaskId(
            self,
            gameId: int,
            externalTaskId: str,
    ):
        with self.session_factory() as session:
            query = session.query(self.model)
            query = query.filter(
                self.model.gameId == gameId, self.model.externalTaskId == externalTaskId).first()
            return query

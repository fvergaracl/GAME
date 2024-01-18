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
        print('-2-')
        with self.session_factory() as session:
            print('-3-')
            schema_as_dict = schema.dict(exclude_none=True)
            ordering = schema_as_dict.get("ordering", configs.ORDERING)
            order_query = (
                getattr(self.model, ordering[1:]).desc()
                if ordering.startswith("-")
                else getattr(self.model, ordering).asc()
            )
            print('-4-')
            page = schema_as_dict.get("page", configs.PAGE)
            page_size = schema_as_dict.get("page_size", configs.PAGE_SIZE)
            filter_options = dict_to_sqlalchemy_filter_options(
                self.model, schema.dict(exclude_none=True))
            query = session.query(self.model)
            print('-5-')
            if eager:
                print('-6-')
                for eager in getattr(self.model, "eagers", []):
                    query = query.options(
                        joinedload(getattr(self.model, eager)))
            filtered_query = query.filter(filter_options)
            query = filtered_query.order_by(order_query)
            print('-7-')
            if page_size == "all":
                query = query.all()
            else:
                query = query.limit(page_size).offset(
                    (page - 1) * page_size).all()
            total_count = filtered_query.count()
            print('-8-')
            return {
                "founds": query,
                "search_options": {
                    "page": page,
                    "page_size": page_size,
                    "ordering": ordering,
                    "total_count": total_count,
                },
            }

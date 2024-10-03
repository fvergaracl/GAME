from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.kpi_metrics import KpiMetrics
from app.repository.base_repository import BaseRepository


class KpiMetricsRepository(BaseRepository):
    """
    Repository class for KPI metrics.

    Attributes:
        session_factory (Callable[..., AbstractContextManager[Session]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for KPI metrics.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractContextManager[Session]],
        model=KpiMetrics,
    ) -> None:
        """
        Initializes the KpiMetricsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for KPI metrics.
        """
        super().__init__(session_factory, model)

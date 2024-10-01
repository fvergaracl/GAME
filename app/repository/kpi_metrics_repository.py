from contextlib import AbstractContextManager
from typing import Callable

from sqlalchemy.orm import Session

from app.model.kpi_metrics import KPIMetrics
from app.repository.base_repository import BaseRepository


class KPIMetricsRepository(BaseRepository):
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
        model=KPIMetrics,
    ) -> None:
        """
        Initializes the KPIMetricsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractContextManager[Session]]):
              The session factory.
            model: The SQLAlchemy model class for KPI metrics.
        """
        super().__init__(session_factory, model)
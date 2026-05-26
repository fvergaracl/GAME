from contextlib import AbstractAsyncContextManager
from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.kpi_metrics import KpiMetrics
from app.repository.base_repository import BaseRepository


class KpiMetricsRepository(BaseRepository):
    """
    Repository class for KPI metrics.

    Attributes:
        session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
          Factory for creating SQLAlchemy sessions.
        model: SQLAlchemy model class for KPI metrics.
    """

    def __init__(
        self,
        session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]],
        model=KpiMetrics,
    ) -> None:
        """
        Initializes the KpiMetricsRepository with the provided session factory
          and model.

        Args:
            session_factory (Callable[..., AbstractAsyncContextManager[AsyncSession]]):
              The session factory.
            model: The SQLAlchemy model class for KPI metrics.
        """
        super().__init__(session_factory, model)

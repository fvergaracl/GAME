from app.repository.kpi_metrics_repository import KpiMetricsRepository
from app.services.base_service import BaseService


class KpiMetricsService(BaseService):
    """
    Service class for KPI metrics.

    Attributes:
        kpi_metrics_repository (KpiMetricsRepository): Repository instance
          for KPI metrics.
    """

    def __init__(self, kpi_metrics_repository: KpiMetricsRepository):
        """
        Initializes the KpiMetricsService with the provided repository.

        Args:
            kpi_metrics_repository (KpiMetricsRepository): The repository
              instance.
        """
        self.kpi_metrics_repository = kpi_metrics_repository
        super().__init__(kpi_metrics_repository)

"""Internal implementation package for :class:`UserPointsService`.

The service used to live in a single ~1100-line module. It has been split by
responsibility into mixins so each concern (persistence, assignment,
simulation, read queries) lives in its own focused module while the public
class ``app.services.user_points_service.UserPointsService`` keeps an
unchanged constructor and method surface.
"""

from app.services.user_points.assignment import PointsAssignmentMixin
from app.services.user_points.persistence import PointsPersistenceMixin
from app.services.user_points.queries import PointsQueryMixin
from app.services.user_points.simulation import PointsSimulationMixin

__all__ = [
    "PointsAssignmentMixin",
    "PointsPersistenceMixin",
    "PointsQueryMixin",
    "PointsSimulationMixin",
]

"""Internal implementation package for :class:`TaskService`.

The service used to live in a single ~1020-line module that mixed the task
read, write and points-by-task concerns and inlined the same
strategy-variable coercion loop five times. It has been split by
responsibility into mixins (plus one shared helper in ``_base``) so each
concern lives in its own focused module, while the public class
``app.services.task_service.TaskService`` keeps an unchanged constructor and
method surface.
"""

from app.services.task.mutations import TaskMutationMixin
from app.services.task.points import TaskPointsMixin
from app.services.task.queries import TaskQueryMixin

__all__ = [
    "TaskMutationMixin",
    "TaskPointsMixin",
    "TaskQueryMixin",
]

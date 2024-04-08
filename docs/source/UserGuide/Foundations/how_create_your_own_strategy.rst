Strategy Creation
-----------------

In GAME, strategies are automatically added to the strategy catalog through a Strategy Plug-In system located in ``app/engine``. All strategies must conform to the base class defined in ``app/engine/base_strategy.py``, and all variables must begin with the prefix ``variable_``. For visual clarity and to facilitate understanding of the strategy and its conditions, it is recommended to include a comment with a strategy diagram at the beginning of the strategy file. You can use the platform https://dreampuf.github.io/GraphvizOnline/ to create the diagram.

Each strategy file must inherit from the ``BaseStrategy`` class, and the file name should correspond to the strategy ID. The gamification logic is defined within the ``calculate_points(self, externalGameId, externalTaskId, externalUserId)`` method. If you need information about a user's or users' previous interactions with a Game or Task, you should define the required service and then use it within the ``calculate_points`` function.

If correctly implemented, the strategy should be displayed in the ``GET /api/v1/strategies`` endpoint when you deploy the REST API. If it does not appear, then there may be an error in the file structure.

**Example Strategy Implementation**:

.. code-block:: python

    """
    # noqa
    Diagram example: https://dreampuf.github.io/GraphvizOnline/#digraph%20G%20%7B%0A%20%20%20%20rankdir...
    """

    from app.engine.base_strategy import BaseStrategy
    from app.core.container import Container

    class SocioBeeStrategy(BaseStrategy):  # noqa
        def __init__(self):
            super().__init__(
                strategy_name="SOCIO_BEE",
                strategy_description="A more advanced gamification strategy with "
                "additional points and penalties.",
                strategy_name_slug="enhanced_gamification",
                strategy_version="0.0.2",
                variable_basic_points=1,
                variable_bonus_points=1,
            )
            self.task_service = Container.task_service()
            self.user_points_service = Container.user_points_service()

            self.debug = True

            self.default_points_task_campaign = 1
            self.variable_basic_points = 1
            self.variable_bonus_points = 10
            self.variable_individual_over_global_points = 3
            self.variable_peak_performer_bonus_points = 15
            self.variable_global_advantage_adjustment_points = 7
            self.variable_individual_adjustment_points = 8

        def calculate_points(self, externalGameId, externalTaskId, externalUserId):
            # Strategy logic goes here

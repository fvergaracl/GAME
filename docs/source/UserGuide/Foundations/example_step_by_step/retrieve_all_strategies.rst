Retrieve All Strategies
-----------------------

To begin, it's necessary to know which strategy you will apply to the game you're creating. For this purpose, you can list all the strategies using the following endpoint.

**Endpoint**: ``GET /api/v1/strategies``

**Example of response**:

.. code-block:: json

    [
      {
        "id": "socio_bee",
        "name": "SOCIO_BEE",
        "description": "A more advanced gamification strategy with additional points and penalties.",
        "version": "0.0.2",
        "variables": {
          "variable_basic_points": 1,
          "variable_bonus_points": 10,
          "variable_individual_over_global_points": 3,
          "variable_peak_performer_bonus_points": 15,
          "variable_global_advantage_adjustment_points": 7,
          "variable_individual_adjustment_points": 8
        }
      },
      {
        "id": "default",
        "name": "EnhancedGamificationStrategy",
        "description": "A more advanced gamification strategy with additional points and penalties.",
        "version": "0.0.2",
        "variables": {
          "variable_basic_points": 1,
          "variable_bonus_points": 10,
          "variable_individual_over_global_points": 3,
          "variable_peak_performer_bonus_points": 15,
          "variable_global_advantage_adjustment_points": 7,
          "variable_individual_adjustment_points": 8
        }
      }
    ]

**Graphical representation**:

.. image:: ../../../static/images/creation_game_example/retrieve_all_strategies.png
    :alt: User Figure
    :align: center
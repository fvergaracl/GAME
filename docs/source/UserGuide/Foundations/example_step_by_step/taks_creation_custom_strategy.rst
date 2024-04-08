Create a Task with a Custom Strategy Independent of the Game
------------------------------------------------------------

After setting up your game, you might want to add tasks that, while inheriting the game's general strategy, use a specific, independent strategy for more tailored gamification approaches. This method allows for custom task-level strategies that may vary from the game's default strategy but still adhere to the overarching gamification framework.

**Endpoint**: ``POST /api/v1/games/{gameId}/tasks``

Ensure to replace ``{gameId}`` with the actual ID of the game to which you're adding the task.

**Request Body**:

.. code-block:: json

    {
      "externalTaskId": "example_task_with_own_strategy",
      "strategyId": "custom_strategy",
      "params": [
        {
          "key": "variable_basic_points",
          "value": 15
        }
      ]
    }

**Example of response**:

.. code-block:: json
  
    {
        "message": "Task created successfully with externalTaskId: example_task_with_own_strategy for gameId: example_game_id",
        "externalTaskId": "example_task_with_own_strategy",
        "externalGameId": "example_game",
        "gameParams": [
            {
            "key": "variable_basic_points",
            "value": "5"
            }
        ],
        "taskParams": [
            {
            "key": "variable_basic_points",
            "value": "15"
            }
        ],
        "strategy": {
            "id": "custom_strategy",
            "name": "Custom Strategy Name",
            "description": "A custom strategy designed for specific task engagement.",
            "version": "1.0.0",
            "variables": {
            "variable_basic_points": 15,
            "variable_bonus_points": 20,
            "variable_individual_over_global_points": 5,
            "variable_peak_performer_bonus_points": 25,
            "variable_global_advantage_adjustment_points": 10,
            "variable_individual_adjustment_points": 12
            }
        }
    }

- **externalTaskId**: A unique identifier for the task, used to identify the task in future interactions.

This request specifies a custom strategy for the task by using the "strategyId" field. Even though a specific strategy is applied, it's crucial to understand:

- **Inheritance of Variables**: Regardless of the defined strategy, variables from the game's default strategy can still be inherited unless explicitly overridden in the task's parameters. In this example, "variable_basic_points" is set to 15, explicitly overriding the game's default or any previously inherited value for this variable.

- **Strategy Independence**: Specifying a "strategyId" allows this task to implement a strategy that is different from the game's default. This enables more nuanced gamification mechanics tailored to the task's specific goals or behaviors, providing a diverse user experience within the same game environment.

This method of task creation enhances the flexibility and depth of the gamification system, allowing for both broad strategy alignment and specific task-level customizations.

**Graphical representation**:

.. image:: ../../../static/images/creation_game_example/task_with_custom_strategy.png
    :alt: Task with Custom Strategy
    :align: center
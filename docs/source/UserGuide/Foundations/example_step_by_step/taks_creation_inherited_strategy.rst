Create task with game strategy 
------------------------------------------

After creating a game, the next step is to add tasks to it. Tasks represent specific activities or actions that users are expected to complete within the game. A task can either inherit the game's overall strategy or be configured with its specific parameters, even if it follows the inherited strategy.

**Endpoint**: ``POST /api/v1/games/{gameId}/tasks``

Replace ``{gameId}`` with the actual ID of the game to which you want to add the task.

**Request Body**:

.. code-block:: json

    {
      "externalTaskId": "example_task",
      "params": [
        {
          "key": "variable_basic_points",
          "value": 10
        }
      ]
    }

**Example of response**:

.. code-block:: json
  
    {
        "message": "Task created successfully with externalTaskId: example_task for gameId: 9b22b0f1-ecbf-442f-9574-222ad9b9e262 ",
        "externalTaskId": "example_task",
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
            "value": "10"
            }
        ],
        "strategy": {
            "id": "default",
            "name": "EnhancedGamificationStrategy",
            "description": "A more advanced gamification strategy with additional points and penalties.",
            "version": "0.0.2",
            "variables": {
            "variable_basic_points": 10,
            "variable_bonus_points": 10,
            "variable_individual_over_global_points": 3,
            "variable_peak_performer_bonus_points": 15,
            "variable_global_advantage_adjustment_points": 7,
            "variable_individual_adjustment_points": 8
            }
        }
    }

- **externalTaskId**: A unique identifier for the task, external to the GAME system. This ID is used to identify the task in the future if necessary.

This request demonstrates how to set a specific value for "variable_basic_points" for a particular task. By doing so, this task is configured to award 10 basic points to users upon completion. It's important to note:

- **Inheriting the Game Strategy**: By not specifying a "strategyId" in the request, the task inherits the strategy of its parent game. If the game's strategy includes a default value for "variable_basic_points", this specific task overrides that default with its own value of 10.

- **Task-Specific Parameters**: The "params" section allows for setting task-specific parameters. In this case, "variable_basic_points" is set to 10, demonstrating that tasks can have unique configurations independent of the game's overall settings or other tasks.

This flexibility in task creation ensures that while tasks can align with the broad gamification strategy of their parent game, they can also be individually tailored to meet specific goals or requirements. This approach allows for a rich and varied user experience within the same game framework.


**Graphical representation**:

.. image:: ../../../static/images/creation_game_example/task_with_Inherited_strategy.png
    :alt: Task with Inherited Game Strategy
    :align: center
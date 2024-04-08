Assign Points to a User in a Game
----------------------------------

After creating tasks within your game, assigning points to users based on their task completion is a crucial next step. Our system offers the flexibility to assign points to users even if they have not been previously registered in the system. If a user does not exist at the time points are assigned, the system will automatically create a profile for them. This ensures that users can have a presence in one or more games without needing explicit prior creation.

**Endpoint**: ``POST /api/v1/games/{gameId}/tasks/{taskId}/points/assign``

To assign points to user "user_1" for completing the task "example_task" in the game with ``gameId`` "9b22b0f1-ecbf-442f-9574-222ad9b9e262", follow the steps below. Remember to replace ``{gameId}`` and ``{taskId}`` with their actual values.

**Request Body**:

.. code-block:: json

    {
      "externalUserId": "user_1",
      "data": {}
    }

**Example of Response**:

.. code-block:: json

    {
      "points": 1,
      "caseName": "BasicEngagement",
      "isACreatedUser": true,
      "gameId": "9b22b0f1-ecbf-442f-9574-222ad9b9e262",
      "externalTaskId": "example_task",
      "created_at": "2024-04-08 12:05:37.161918+00:00"
    }

- **externalUserId**: The identifier for the user receiving points. If "user_1" does not exist, the system will automatically create a new profile for them.

- **caseName**: Represents the name of the condition within the strategy that was met to assign points. This field helps identify which conditions were fulfilled to award points under the game's strategy.

- **isACreatedUser**: This boolean indicates whether the user was created as part of this point assignment process (true if the user was not previously registered and was thus created, false otherwise).

This response confirms that points were successfully assigned, providing details about the transaction. It includes whether a new user profile was created, aligning with the system's ability to dynamically integrate users into the game environment. This feature ensures a seamless and inclusive gamification strategy, accommodating dynamic user engagement across multiple games and tasks without the need for prior user setup or registration.



.. image:: ../../../static/images/creation_game_example/assign_points_user_1.png
    :alt:  Assign Points to a User in a Game
    :align: center
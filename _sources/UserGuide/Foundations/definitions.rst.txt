GAME Definitions
===============================

This section provides a detailed description of the key components within the gamification system, including platforms, games, tasks, points, coins, and wallets.

Platform
--------

A **Platform** is the digital environment or service that hosts multiple **Games**. Each Platform is characterized by its unique name and serves as a container for organizing and managing related Games.

.. image:: ../../../static/images/platform.png
    :alt: Platform Figure

Game
----

A **Game** acts as an individual campaign or project within a Platform. Each Game is autonomous and may include one or more **Tasks** targeted at users. Games can implement specific strategies for the gamification of user actions. If a strategy is not specified for a Game, a default strategy named "default" is applied.

.. image:: ../../../static/images/game.png
    :alt: Game Figure


Task
----

A **Task** is a specific activity or action assigned to users for completion within a Game. Each Task is evaluated according to a gamification strategy, inheriting the strategy of the Game to which it belongs unless specified otherwise. Tasks are designed to be independent of each other.

.. image:: ../../../static/images/task.png
    :alt: Task Figure

Points
------

**Points** represent the rewards awarded to users for completing Tasks within a Game. The amount of Points awarded is determined by the gamification strategy applied to the Task or Game.

.. image:: ../../../static/images/points.png
    :alt: Points Figure


Coins
-----

**Coins** are a form of digital currency that users can obtain in exchange for their Points. This exchange is governed by a specific conversion rate, allowing users to redeem accumulated Points for Coins within the system.

.. image:: ../../../static/images/coins.png
    :alt: Coins Figure

Wallet
------

A **Wallet** is a digital component associated with each user that records and manages the user's Points and Coins balance. Wallets allow users to view their balance and perform operations like exchanging Points for Coins.

.. image:: ../../../static/images/wallet.png
    :alt: Wallet Figure


Additional Definitions
----------------------

Gamification Strategy
^^^^^^^^^^^^^^^^^^^^^

Defines the set of rules and mechanisms that determine how Points and rewards are awarded to users for performing Tasks within a Game. Strategies can vary between Games and can be customized to achieve different engagement objectives.

.. image:: ../../../static/images/strategy.png
    :alt: Strategy Figure


User
^^^^

Represents a person who interacts with the Games on the Platform, completing Tasks to earn Points and, potentially, exchange them for Coins. Each user has an associated Wallet that tracks their Points and Coins.


.. image:: ../../../static/images/user.png
    :alt: User Figure

Conversion Rate
^^^^^^^^^^^^^^^

The ratio that defines how many Points are needed to obtain a Coin. This rate can be fixed or vary based on different factors, such as promotions or the user's level of activity.

Transaction
^^^^^^^^^^^


.. image:: ../../../static/images/transaction.png
    :alt: Transaction Figure

A record of any operation performed within the system, such as the allocation of Points for completing a Task, the exchange of Points for Coins, or any other activity that affects a user's Wallet balance.

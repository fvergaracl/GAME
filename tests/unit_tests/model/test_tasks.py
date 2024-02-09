import pytest
from datetime import datetime, timezone
from app.model.tasks import Tasks
from uuid import uuid4


def test_tasks_creation_and_representation():
    now = datetime.now(timezone.utc)
    game_id = str(uuid4())
    strategy_id = str(uuid4())

    task = Tasks(
        created_at=now,
        updated_at=now,
        externalTaskId="external_task_123",
        gameId=game_id,
        strategyId=strategy_id
    )

    expected_str = (
        f"Tasks(id={task.id}, created_at={now}, updated_at={now}, "
        f"externalTaskId=external_task_123, gameId={game_id}, strategyId={strategy_id})"
    )
    assert str(task) == expected_str
    assert repr(task) == expected_str


def test_tasks_equality():
    game_id = str(uuid4())
    strategy_id = str(uuid4())

    task1 = Tasks(
        externalTaskId="task_123",
        gameId=game_id,
        strategyId=strategy_id
    )
    task2 = Tasks(
        externalTaskId="task_123",
        gameId=game_id,
        strategyId=strategy_id
    )
    task3 = Tasks(
        externalTaskId="task_124",
        gameId=str(uuid4()),  # Different game ID
        strategyId=str(uuid4())  # Different strategy ID
    )

    # Even if externalTaskId, gameId, and strategyId match, tasks are unique by their id
    assert task1 != task2
    # Different attributes should lead to inequality
    assert task1 != task3


def test_tasks_hash():
    game_id = str(uuid4())
    strategy_id = str(uuid4())

    task1 = Tasks(
        externalTaskId="task_123",
        gameId=game_id,
        strategyId=strategy_id
    )

    game_id_2 = str(uuid4())
    strategy_id_2 = str(uuid4())

    task2 = Tasks(
        externalTaskId="task_123",
        gameId=game_id_2,
        strategyId=strategy_id_2
    )

    # Hashes rely on externalTaskId, gameId, and strategyId, but unique id should differentiate them
    assert hash(task1) != hash(task2)

    task2.id = task1.id
    task2.gameId = game_id
    task2.strategyId = strategy_id
    assert hash(task1) == hash(task2)


if __name__ == "__main__":
    pytest.main()

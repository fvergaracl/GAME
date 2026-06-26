"""
Integration tests for ``UserPointsRepository``.

The repository contains a wide range of read paths. Postgres-only methods
(those depending on ``func.array_agg``, ``func.json_build_object`` or
``UserPoints.data["..."].as_float``) are out of scope for aiosqlite; this
module covers the rest end-to-end against an in-memory aiosqlite engine.
"""

import pytest

from app.model.games import Games
from app.model.tasks import Tasks
from app.model.user_points import UserPoints
from app.model.users import Users
from app.repository.user_points_repository import UserPointsRepository


@pytest.fixture
def repository(session_factory):
    return UserPointsRepository(session_factory=session_factory)


async def _seed_user(db_session, external_id):
    user = Users(externalUserId=external_id)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_game(db_session, external_id="g-1"):
    game = Games(externalGameId=external_id, platform="web", strategyId="default")
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


async def _seed_task(db_session, game_id, external_task_id):
    task = Tasks(
        externalTaskId=external_task_id,
        gameId=game_id,
        strategyId="default",
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


async def _seed_points(
    db_session, user_id, task_id, points, idempotency_key=None, data=None
):
    point = UserPoints(
        userId=user_id,
        taskId=task_id,
        points=points,
        idempotencyKey=idempotency_key,
        data=data,
    )
    db_session.add(point)
    await db_session.commit()
    await db_session.refresh(point)
    return point


def test_repository_exposes_helper_repositories(repository):
    assert repository.task_repository.model is Tasks
    assert repository.user_repository.model is Users


@pytest.mark.asyncio
async def test_get_first_user_points_returns_a_row_when_present(repository, db_session):
    user = await _seed_user(db_session, "ext-fp")
    game = await _seed_game(db_session, "g-fp")
    task = await _seed_task(db_session, game.id, "task-fp")
    await _seed_points(db_session, user.id, task.id, points=10, idempotency_key="k1")

    result = await repository.get_first_user_points_in_external_task_id_by_user_id(
        externalTaskId="task-fp",
        externalUserId="ext-fp",
    )

    assert result is not None
    assert result.points == 10


@pytest.mark.asyncio
async def test_get_first_user_points_returns_none_when_missing(repository):
    result = await repository.get_first_user_points_in_external_task_id_by_user_id(
        externalTaskId="absent",
        externalUserId="absent",
    )
    assert result is None


@pytest.mark.asyncio
async def test_read_by_user_task_and_idempotency_returns_match(repository, db_session):
    user = await _seed_user(db_session, "ext-idem")
    game = await _seed_game(db_session, "g-idem")
    task = await _seed_task(db_session, game.id, "task-idem")
    point = await _seed_points(
        db_session, user.id, task.id, points=5, idempotency_key="abc-123"
    )

    result = await repository.read_by_user_task_and_idempotency(
        user_id=user.id, task_id=task.id, idempotency_key="abc-123"
    )

    assert result is not None
    assert result.id == point.id


@pytest.mark.asyncio
async def test_read_by_user_task_and_idempotency_short_circuits_empty_key(
    repository,
):
    """
    Returns ``None`` immediately for empty idempotency keys so a missing key
    never coincidentally matches a row with NULL ``idempotencyKey``.
    """
    result = await repository.read_by_user_task_and_idempotency(
        user_id="any", task_id="any", idempotency_key=""
    )
    assert result is None


@pytest.mark.asyncio
async def test_read_by_user_task_and_idempotency_returns_none_when_missing(
    repository, db_session
):
    user = await _seed_user(db_session, "ext-no-match")
    game = await _seed_game(db_session, "g-no-match")
    task = await _seed_task(db_session, game.id, "task-no-match")

    result = await repository.read_by_user_task_and_idempotency(
        user_id=user.id, task_id=task.id, idempotency_key="never-stored"
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_user_measurement_count_counts_per_user(repository, db_session):
    user = await _seed_user(db_session, "ext-meas")
    game = await _seed_game(db_session, "g-meas")
    task = await _seed_task(db_session, game.id, "task-meas")
    for i in range(3):
        await _seed_points(
            db_session, user.id, task.id, points=i, idempotency_key=f"k-{i}"
        )

    count = await repository.get_user_measurement_count(user.id)

    assert count == 3


@pytest.mark.asyncio
async def test_get_individual_calculation_returns_avg_points(repository, db_session):
    user = await _seed_user(db_session, "ext-avg")
    game = await _seed_game(db_session, "g-avg")
    task = await _seed_task(db_session, game.id, "task-avg")
    for i, p in enumerate([2, 4, 6]):
        await _seed_points(
            db_session, user.id, task.id, points=p, idempotency_key=f"k-{i}"
        )

    avg = await repository.get_individual_calculation(user.id)

    assert avg == 4.0


@pytest.mark.asyncio
async def test_get_global_calculation_returns_avg_across_all(repository, db_session):
    user = await _seed_user(db_session, "ext-glob")
    game = await _seed_game(db_session, "g-glob")
    task = await _seed_task(db_session, game.id, "task-glob")
    for i, p in enumerate([10, 20, 30]):
        await _seed_points(
            db_session, user.id, task.id, points=p, idempotency_key=f"k-{i}"
        )

    avg = await repository.get_global_calculation()

    assert avg == 20.0


@pytest.mark.asyncio
async def test_get_start_and_last_task_times(repository, db_session):
    user = await _seed_user(db_session, "ext-time")
    game = await _seed_game(db_session, "g-time")
    task = await _seed_task(db_session, game.id, "task-time")
    await _seed_points(db_session, user.id, task.id, points=1, idempotency_key="k-1")
    await _seed_points(db_session, user.id, task.id, points=2, idempotency_key="k-2")

    start = await repository.get_start_time_for_last_task(user.id)
    last = await repository.get_time_taken_for_last_task(user.id)

    assert start is not None
    assert last is not None
    assert last >= start


@pytest.mark.asyncio
async def test_get_task_by_external_user_id_returns_user_tasks(repository, db_session):
    user = await _seed_user(db_session, "ext-task-list")
    game = await _seed_game(db_session, "g-task-list")
    task = await _seed_task(db_session, game.id, "task-list-1")
    await _seed_points(db_session, user.id, task.id, points=1, idempotency_key="k")

    tasks = await repository.get_task_by_externalUserId("ext-task-list")

    assert any(t.externalTaskId == "task-list-1" for t in tasks)


@pytest.mark.asyncio
async def test_get_last_task_by_user_id_returns_some_row(repository, db_session):
    user = await _seed_user(db_session, "ext-last")
    game = await _seed_game(db_session, "g-last")
    task = await _seed_task(db_session, game.id, "task-last")
    await _seed_points(db_session, user.id, task.id, points=1, idempotency_key="old")
    await _seed_points(db_session, user.id, task.id, points=2, idempotency_key="new")

    result = await repository.get_last_task_by_userId(user.id)

    assert result is not None
    assert result.points in {1, 2}


@pytest.mark.asyncio
async def test_count_measurements_by_external_task_id(repository, db_session):
    user = await _seed_user(db_session, "ext-cnt")
    game = await _seed_game(db_session, "g-cnt")
    task = await _seed_task(db_session, game.id, "task-cnt")
    for i in range(4):
        await _seed_points(
            db_session, user.id, task.id, points=i, idempotency_key=f"k-{i}"
        )

    count = await repository.count_measurements_by_external_task_id("task-cnt")

    assert count == 4


@pytest.mark.asyncio
async def test_user_has_record_in_last_minutes_true_when_recent(repository, db_session):
    user = await _seed_user(db_session, "ext-recent")
    game = await _seed_game(db_session, "g-recent")
    task = await _seed_task(db_session, game.id, "task-recent")
    await _seed_points(db_session, user.id, task.id, points=1, idempotency_key="k")

    result = await repository.user_has_record_before_in_externalTaskId_last_min(
        externalTaskId="task-recent",
        externalUserId="ext-recent",
        minutes=60,
    )

    assert result is True


@pytest.mark.asyncio
async def test_get_user_task_measurements_returns_timestamps(repository, db_session):
    user = await _seed_user(db_session, "ext-ts")
    game = await _seed_game(db_session, "g-ts")
    task = await _seed_task(db_session, game.id, "task-ts")
    for i in range(3):
        await _seed_points(
            db_session, user.id, task.id, points=i, idempotency_key=f"k-{i}"
        )

    timestamps = await repository.get_user_task_measurements(
        externalTaskId="task-ts",
        externalUserId="ext-ts",
    )

    assert len(timestamps) == 3


@pytest.mark.asyncio
async def test_get_user_task_measurements_count(repository, db_session):
    user = await _seed_user(db_session, "ext-cn")
    game = await _seed_game(db_session, "g-cn")
    task = await _seed_task(db_session, game.id, "task-cn")
    for i in range(2):
        await _seed_points(
            db_session, user.id, task.id, points=i, idempotency_key=f"k-{i}"
        )

    count = await repository.get_user_task_measurements_count(
        externalTaskId="task-cn",
        externalUserId="ext-cn",
    )

    assert count == 2


@pytest.mark.asyncio
async def test_count_personal_records_by_external_game_id(repository, db_session):
    user = await _seed_user(db_session, "ext-pr")
    game = await _seed_game(db_session, "g-pr-ext")
    task = await _seed_task(db_session, game.id, "task-pr")
    for i in range(2):
        await _seed_points(
            db_session, user.id, task.id, points=i, idempotency_key=f"k-{i}"
        )

    count = await repository.count_personal_records_by_external_game_id(
        externalGameId="g-pr-ext", externalUserId="ext-pr"
    )

    assert count == 2


@pytest.mark.asyncio
async def test_get_avg_time_between_tasks_returns_minus_one_with_few_rows(
    repository, db_session
):
    user = await _seed_user(db_session, "ext-avg-time")
    game = await _seed_game(db_session, "g-avg-time")
    task = await _seed_task(db_session, game.id, "task-avg-time")
    await _seed_points(db_session, user.id, task.id, points=1, idempotency_key="k")

    result = await repository.get_avg_time_between_tasks_for_all_users(
        externalGameId="g-avg-time",
        externalTaskId="task-avg-time",
    )

    assert result == -1


@pytest.mark.asyncio
async def test_get_last_window_time_diff_returns_zero_when_under_two_points(
    repository, db_session
):
    user = await _seed_user(db_session, "ext-win-zero")
    game = await _seed_game(db_session, "g-win-zero")
    task = await _seed_task(db_session, game.id, "task-win-zero")
    await _seed_points(db_session, user.id, task.id, points=1, idempotency_key="k")

    diff = await repository.get_last_window_time_diff(
        externalTaskId="task-win-zero",
        externalUserId="ext-win-zero",
    )

    assert diff == 0


@pytest.mark.asyncio
async def test_get_all_point_of_tasks_list_returns_only_listed_tasks(
    repository, db_session
):
    user = await _seed_user(db_session, "ext-list")
    game = await _seed_game(db_session, "g-list")
    task_a = await _seed_task(db_session, game.id, "task-list-a")
    task_b = await _seed_task(db_session, game.id, "task-list-b")
    await _seed_points(db_session, user.id, task_a.id, points=1, idempotency_key="ka")
    await _seed_points(db_session, user.id, task_b.id, points=2, idempotency_key="kb")

    results = await repository.get_all_point_of_tasks_list([task_a.id])

    assert len(results) == 1


@pytest.mark.asyncio
async def test_get_all_point_of_tasks_list_with_data_returns_full_objects(
    repository, db_session
):
    user = await _seed_user(db_session, "ext-list-data")
    game = await _seed_game(db_session, "g-list-data")
    task = await _seed_task(db_session, game.id, "task-list-data")
    await _seed_points(
        db_session,
        user.id,
        task.id,
        points=1,
        idempotency_key="k",
        data={"meta": "abc"},
    )

    results = await repository.get_all_point_of_tasks_list([task.id], withData=True)

    assert len(results) == 1
    assert results[0].data == {"meta": "abc"}

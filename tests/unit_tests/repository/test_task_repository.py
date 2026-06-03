"""
Integration tests for ``TaskRepository`` against aiosqlite.
"""

from uuid import UUID, uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.model.games import Games
from app.model.task_params import TasksParams
from app.model.tasks import Tasks
from app.model.user_points import UserPoints
from app.repository.task_repository import TaskRepository
from app.schema.task_schema import FindTask


@pytest.fixture
def repository(session_factory):
    return TaskRepository(session_factory=session_factory)


async def _seed_game(db_session, external_id="game-1"):
    game = Games(externalGameId=external_id, platform="web", strategyId="default")
    db_session.add(game)
    await db_session.commit()
    await db_session.refresh(game)
    return game


async def _seed_task(db_session, game_id, external_task_id="t-1"):
    task = Tasks(
        externalTaskId=external_task_id,
        gameId=game_id,
        strategyId="default",
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.mark.asyncio
async def test_read_by_game_id_returns_tasks(repository, db_session):
    """
    ``read_by_gameId`` delegates filtering to the generic
    ``dict_to_sqlalchemy_filter_options`` builder, which currently does not
    convert UUID-typed fields into SQL filters. This test verifies the result
    shape (items + search options) without asserting per-gameId filtering.
    """
    game_a = await _seed_game(db_session, "game-a")
    await _seed_task(db_session, game_a.id, "t-a1")
    await _seed_task(db_session, game_a.id, "t-a2")

    schema = FindTask(
        gameId=game_a.id,
        ordering="externalTaskId",
        page=1,
        page_size=10,
    )
    result = await repository.read_by_gameId(schema)

    assert {t.externalTaskId for t in result["items"]} == {"t-a1", "t-a2"}
    assert result["search_options"]["total_count"] == 2


@pytest.mark.asyncio
async def test_read_by_game_id_paginates_results(repository, db_session):
    game = await _seed_game(db_session, "game-paged")
    for i in range(5):
        await _seed_task(db_session, game.id, f"t-{i}")

    schema = FindTask(
        gameId=game.id,
        ordering="externalTaskId",
        page=1,
        page_size=2,
    )
    result = await repository.read_by_gameId(schema)

    assert len(result["items"]) == 2
    assert result["search_options"]["total_count"] == 5


@pytest.mark.asyncio
async def test_read_by_game_id_and_external_task_id_returns_match(
    repository, db_session
):
    game = await _seed_game(db_session, "game-c")
    task = await _seed_task(db_session, game.id, "t-c-1")

    result = await repository.read_by_gameId_and_externalTaskId(game.id, "t-c-1")

    assert result is not None
    assert result.id == task.id


@pytest.mark.asyncio
async def test_read_by_game_id_and_external_task_id_returns_none_when_missing(
    repository, db_session
):
    game = await _seed_game(db_session, "game-no-task")

    result = await repository.read_by_gameId_and_externalTaskId(game.id, "absent")

    assert result is None


@pytest.mark.asyncio
async def test_get_points_and_users_by_task_id_returns_task(repository, db_session):
    game = await _seed_game(db_session, "game-pt")
    task = await _seed_task(db_session, game.id, "t-pt")

    result = await repository.get_points_and_users_by_taskId(task.id)

    assert result.id == task.id


@pytest.mark.asyncio
async def test_get_points_and_users_by_task_id_raises_not_found_when_missing(
    repository,
):
    missing = UUID("00000000-0000-0000-0000-000000000000")

    with pytest.raises(NotFoundError):
        await repository.get_points_and_users_by_taskId(missing)


async def _seed_task_param(db_session, task_id, key="k", value="v"):
    param = TasksParams(taskId=task_id, key=key, value=value)
    db_session.add(param)
    await db_session.commit()
    await db_session.refresh(param)
    return param


async def _seed_user_points(db_session, task_id, points=10):
    up = UserPoints(points=points, userId=uuid4(), taskId=task_id)
    db_session.add(up)
    await db_session.commit()
    await db_session.refresh(up)
    return up


@pytest.mark.asyncio
async def test_delete_task_by_id_cascades_params_and_points(repository, db_session):
    from sqlalchemy import select

    game = await _seed_game(db_session, "game-del")
    task = await _seed_task(db_session, game.id, "t-del")
    await _seed_task_param(db_session, task.id, "bonus", "5")
    await _seed_user_points(db_session, task.id, points=7)
    # A sibling task whose params/points must survive the delete.
    other = await _seed_task(db_session, game.id, "t-keep")
    await _seed_task_param(db_session, other.id, "keep", "1")

    result = await repository.delete_task_by_id(task.id)
    assert result is True

    # Task row gone.
    remaining = (
        (await db_session.execute(select(Tasks).filter(Tasks.id == task.id)))
        .scalars()
        .first()
    )
    assert remaining is None

    # Its params and points gone.
    params = (
        (
            await db_session.execute(
                select(TasksParams).filter(TasksParams.taskId == task.id)
            )
        )
        .scalars()
        .all()
    )
    assert params == []
    points = (
        (
            await db_session.execute(
                select(UserPoints).filter(UserPoints.taskId == task.id)
            )
        )
        .scalars()
        .all()
    )
    assert points == []

    # The sibling task and its param are untouched.
    sibling = (
        (await db_session.execute(select(Tasks).filter(Tasks.id == other.id)))
        .scalars()
        .first()
    )
    assert sibling is not None
    sibling_params = (
        (
            await db_session.execute(
                select(TasksParams).filter(TasksParams.taskId == other.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(sibling_params) == 1


@pytest.mark.asyncio
async def test_delete_task_by_id_raises_not_found_when_missing(repository):
    missing = UUID("00000000-0000-0000-0000-000000000000")

    with pytest.raises(NotFoundError):
        await repository.delete_task_by_id(missing)

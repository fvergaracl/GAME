"""
Integration tests for ``UserActionsRepository``.
"""

import pytest

from app.model.user_actions import UserActions
from app.model.users import Users
from app.repository.base_repository import BaseRepository
from app.repository.user_actions_repository import UserActionsRepository
from app.schema.task_schema import AddActionDidByUserInTask


@pytest.fixture
def repository(session_factory):
    return UserActionsRepository(session_factory=session_factory)


def test_init_sets_default_model_and_helper(repository):
    assert repository.model is UserActions
    assert isinstance(repository.userAction_repository, BaseRepository)


@pytest.mark.asyncio
async def test_add_action_in_task_persists_action(repository, db_session):
    user = Users(externalUserId="ext-ua-1")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    payload = AddActionDidByUserInTask(
        typeAction="measurement",
        data={"steps": 10},
        description="user sent measurement",
        externalUserId="ext-ua-1",
    )

    result = await repository.add_action_in_task(
        user_id=user.id, task_id="ignored-by-model", action=payload
    )

    assert result.id is not None
    assert result.typeAction == "measurement"
    assert result.data == {"steps": 10}
    assert result.description == "user sent measurement"
    assert str(result.userId) == str(user.id)

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.model.user_actions import UserActions
from app.repository.base_repository import BaseRepository
from app.repository.user_actions_repository import UserActionsRepository
from app.schema.task_schema import AddActionDidByUserInTask


class TestUserActionsRepository(unittest.TestCase):
    def _build_repository(self):
        session = MagicMock()
        context_manager = MagicMock()
        context_manager.__enter__.return_value = session
        context_manager.__exit__.return_value = False
        session_factory = MagicMock(return_value=context_manager)
        repository = UserActionsRepository(session_factory=session_factory)
        return repository, session

    def test_init_sets_internal_repository_and_model(self):
        repository, _ = self._build_repository()

        self.assertIs(repository.model, UserActions)
        self.assertIsInstance(repository.userAction_repository, BaseRepository)
        self.assertIs(repository.userAction_repository.model, UserActions)

    def test_add_action_in_task_creates_action_and_commits_session(self):
        repository, session = self._build_repository()
        persisted_action = SimpleNamespace(id="action-1")
        repository.model = MagicMock(return_value=persisted_action)
        payload = AddActionDidByUserInTask(
            typeAction="measurement",
            data={"steps": 10},
            description="User sent measurement",
            externalUserId="external-user-1",
        )

        result = repository.add_action_in_task("user-1", "task-1", payload)

        repository.model.assert_called_once_with(
            userId="user-1",
            taskId="task-1",
            typeAction="measurement",
            data={"steps": 10},
            description="User sent measurement",
        )
        session.add.assert_called_once_with(persisted_action)
        session.commit.assert_called_once()
        self.assertIs(result, persisted_action)


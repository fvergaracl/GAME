import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.exceptions import GoneError
from app.repository.game_repository import GameRepository
from app.repository.task_repository import TaskRepository
from app.repository.user_actions_repository import UserActionsRepository
from app.repository.user_repository import UserRepository
from app.schema.task_schema import AddActionDidByUserInTask
from app.schema.user_actions_schema import CreateUserBodyActions
from app.services.user_actions_service import UserActionsService


class TestUserActionsService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_actions_repository = MagicMock(spec=UserActionsRepository)
        self.users_repository = MagicMock(spec=UserRepository)
        self.game_repository = MagicMock(spec=GameRepository)
        self.task_repository = MagicMock(spec=TaskRepository)

        self.service = UserActionsService(
            user_actions_repository=self.user_actions_repository,
            users_repository=self.users_repository,
            game_repository=self.game_repository,
            task_repository=self.task_repository,
        )

    def test_init_sets_repositories(self):
        self.assertIs(
            self.service.user_actions_repository, self.user_actions_repository
        )
        self.assertIs(self.service.users_repository, self.users_repository)
        self.assertIs(self.service.game_repository, self.game_repository)
        self.assertIs(self.service.task_repository, self.task_repository)
        self.assertIs(self.service._repository, self.user_actions_repository)

    async def test_user_add_action_in_task_creates_new_user_when_missing(self):
        game_id = uuid4()
        user_id = uuid4()
        action_id = uuid4()
        self.users_repository.read_by_column.return_value = None
        self.game_repository.read_by_column.return_value = SimpleNamespace(id=game_id)
        self.users_repository.create_user_by_externalUserId = AsyncMock(
            return_value=SimpleNamespace(id=user_id, externalUserId="new_user")
        )
        self.task_repository.read_by_column.return_value = SimpleNamespace(
            status="open"
        )

        created_action_data = {
            "id": action_id,
            "created_at": datetime(2026, 2, 1, 10, 0, 0),
            "updated_at": datetime(2026, 2, 1, 10, 5, 0),
            "typeAction": "click",
            "data": {"k": 1},
            "description": "action-desc",
        }
        self.user_actions_repository.create = AsyncMock(
            return_value=SimpleNamespace(dict=lambda: created_action_data)
        )

        action = AddActionDidByUserInTask(
            typeAction="click",
            data={"k": 1},
            description="action-desc",
            externalUserId="new_user",
        )
        result = await self.service.user_add_action_in_task(
            str(game_id),
            "task-ext-1",
            action,
            api_key="api-key-1",
        )

        self.assertEqual(result.externalUserId, "new_user")
        self.assertEqual(result.typeAction, "click")
        self.assertEqual(result.message, "Action added successfully")
        self.users_repository.create_user_by_externalUserId.assert_awaited_once_with(
            externalUserId="new_user"
        )
        created_payload = self.user_actions_repository.create.await_args.args[0]
        self.assertEqual(created_payload.userId, str(user_id))
        self.assertEqual(created_payload.apiKey_used, "api-key-1")

    async def test_user_add_action_in_task_uses_existing_user(self):
        game_id = uuid4()
        user_id = uuid4()
        action_id = uuid4()
        existing_user = SimpleNamespace(id=user_id, externalUserId="existing_user")
        self.users_repository.read_by_column.return_value = existing_user
        self.game_repository.read_by_column.return_value = SimpleNamespace(id=game_id)
        self.users_repository.create_user_by_externalUserId = AsyncMock()
        self.task_repository.read_by_column.return_value = SimpleNamespace(
            status="open"
        )
        self.user_actions_repository.create = AsyncMock(
            return_value=SimpleNamespace(
                dict=lambda: {
                    "id": action_id,
                    "created_at": datetime(2026, 2, 2, 10, 0, 0),
                    "updated_at": datetime(2026, 2, 2, 10, 5, 0),
                    "typeAction": "view",
                    "data": {"screen": "dashboard"},
                    "description": "viewed dashboard",
                }
            )
        )

        action = AddActionDidByUserInTask(
            typeAction="view",
            data={"screen": "dashboard"},
            description="viewed dashboard",
            externalUserId="existing_user",
        )
        result = await self.service.user_add_action_in_task(
            str(game_id), "task-ext-2", action
        )

        self.assertEqual(result.externalUserId, "existing_user")
        self.users_repository.create_user_by_externalUserId.assert_not_called()
        created_payload = self.user_actions_repository.create.await_args.args[0]
        self.assertEqual(created_payload.userId, str(user_id))
        self.assertIsNone(created_payload.apiKey_used)

    async def test_user_add_action_in_task_raises_when_task_is_not_open(self):
        game_id = uuid4()
        user_id = uuid4()
        self.users_repository.read_by_column.return_value = SimpleNamespace(id=user_id)
        self.game_repository.read_by_column.return_value = SimpleNamespace(id=game_id)
        self.task_repository.read_by_column.return_value = SimpleNamespace(
            status="closed"
        )
        action = AddActionDidByUserInTask(
            typeAction="click",
            data={"k": 2},
            description="closed task action",
            externalUserId="user_closed",
        )

        with self.assertRaises(GoneError):
            await self.service.user_add_action_in_task(
                str(game_id), "task-ext-3", action
            )

        self.user_actions_repository.create.assert_not_called()

    async def test_user_add_action_default_creates_user_when_missing(self):
        user_id = uuid4()
        self.users_repository.read_by_column.return_value = None
        self.users_repository.create_user_by_externalUserId = AsyncMock(
            return_value=SimpleNamespace(id=user_id, externalUserId="new_user")
        )
        self.user_actions_repository.create = AsyncMock(
            return_value=SimpleNamespace(
                typeAction="default_action",
                description="default description",
            )
        )
        schema = CreateUserBodyActions(
            typeAction="default_action",
            data={"minutes": 5},
            description="default description",
            apiKey_used="api-key-2",
        )

        result = await self.service.user_add_action_default(
            externalUserId="new_user",
            schema=schema,
            api_key="api-key-2",
        )

        self.assertEqual(result.userId, str(user_id))
        self.assertTrue(result.is_user_created)
        self.assertEqual(result.typeAction, "default_action")
        self.users_repository.create_user_by_externalUserId.assert_awaited_once_with(
            externalUserId="new_user"
        )

    async def test_user_add_action_default_with_existing_user(self):
        user_id = uuid4()
        self.users_repository.read_by_column.return_value = SimpleNamespace(
            id=user_id, externalUserId="existing_user"
        )
        self.users_repository.create_user_by_externalUserId = AsyncMock()
        self.user_actions_repository.create = AsyncMock(
            return_value=SimpleNamespace(
                typeAction="default_action",
                description="existing user action",
            )
        )
        schema = CreateUserBodyActions(
            typeAction="default_action",
            data={"points": 10},
            description="existing user action",
            apiKey_used=None,
        )

        result = await self.service.user_add_action_default(
            externalUserId="existing_user",
            schema=schema,
        )

        self.assertEqual(result.userId, str(user_id))
        self.assertFalse(result.is_user_created)
        self.assertEqual(result.message, "Action added successfully")
        self.users_repository.create_user_by_externalUserId.assert_not_called()
        created_payload = self.user_actions_repository.create.await_args.args[0]
        self.assertEqual(created_payload.userId, str(user_id))


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from app.repository.task_params_repository import TaskParamsRepository
from app.services.task_params_service import TaskParamsService


class TestTaskParamsService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.task_params_repository = MagicMock(spec=TaskParamsRepository)
        self.service = TaskParamsService(self.task_params_repository)

    def test_init_sets_repositories(self):
        self.assertIs(self.service.task_params_repository, self.task_params_repository)
        self.assertIs(self.service._repository, self.task_params_repository)

    def test_get_list_delegates_to_repository(self):
        schema = {"page": 1}
        expected = {"items": [], "search_options": {"page": 1}}
        self.task_params_repository.read_by_options.return_value = expected

        result = self.service.get_list(schema)

        self.task_params_repository.read_by_options.assert_called_once_with(schema)
        self.assertEqual(result, expected)

    def test_get_by_id_delegates_to_repository(self):
        item_id = uuid4()
        expected = {"id": str(item_id)}
        self.task_params_repository.read_by_id.return_value = expected

        result = self.service.get_by_id(item_id)

        self.task_params_repository.read_by_id.assert_called_once_with(item_id)
        self.assertEqual(result, expected)

    async def test_add_delegates_to_repository_create(self):
        schema = {"taskId": "task-1", "key": "difficulty", "value": "hard"}
        expected = {"id": "param-1"}
        self.task_params_repository.create.return_value = expected

        result = await self.service.add(schema)

        self.task_params_repository.create.assert_awaited_once_with(schema)
        self.assertEqual(result, expected)

    async def test_patch_delegates_to_repository_update(self):
        item_id = uuid4()
        schema = {"value": "expert"}
        expected = {"id": str(item_id), "value": "expert"}
        self.task_params_repository.update.return_value = expected

        result = await self.service.patch(item_id, schema)

        self.task_params_repository.update.assert_awaited_once_with(item_id, schema)
        self.assertEqual(result, expected)

    def test_patch_attr_delegates_to_repository_update_attr(self):
        item_id = uuid4()
        expected = {"id": str(item_id), "value": "normal"}
        self.task_params_repository.update_attr.return_value = expected

        result = self.service.patch_attr(item_id, "value", "normal")

        self.task_params_repository.update_attr.assert_called_once_with(
            item_id, "value", "normal"
        )
        self.assertEqual(result, expected)

    def test_put_update_delegates_to_repository_whole_update(self):
        item_id = uuid4()
        schema = {"taskId": "task-1", "key": "difficulty", "value": "normal"}
        expected = {"id": str(item_id), **schema}
        self.task_params_repository.whole_update.return_value = expected

        result = self.service.put_update(item_id, schema)

        self.task_params_repository.whole_update.assert_called_once_with(
            item_id, schema
        )
        self.assertEqual(result, expected)

    def test_remove_by_id_delegates_to_repository_delete_by_id(self):
        item_id = uuid4()
        self.task_params_repository.delete_by_id.return_value = None

        result = self.service.remove_by_id(item_id)

        self.task_params_repository.delete_by_id.assert_called_once_with(item_id)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

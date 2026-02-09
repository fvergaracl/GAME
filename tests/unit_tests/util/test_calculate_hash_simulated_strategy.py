import unittest

from app.util.calculate_hash_simulated_strategy import calculate_hash_simulated_strategy


class TestCalculateHashSimulatedStrategy(unittest.TestCase):
    def test_same_input_returns_same_hash(self):
        tasks_simulated = [{"externalTaskId": "t1", "points": 10}]
        game_id = "game-1"
        external_user_id = "user-1"

        hash_1 = calculate_hash_simulated_strategy(
            tasks_simulated, game_id, external_user_id
        )
        hash_2 = calculate_hash_simulated_strategy(
            tasks_simulated, game_id, external_user_id
        )

        self.assertEqual(hash_1, hash_2)
        self.assertEqual(len(hash_1), 64)

    def test_different_tasks_return_different_hash(self):
        base_tasks = [{"externalTaskId": "t1", "points": 10}]
        changed_tasks = [{"externalTaskId": "t1", "points": 11}]

        hash_base = calculate_hash_simulated_strategy(base_tasks, "game-1", "user-1")
        hash_changed = calculate_hash_simulated_strategy(
            changed_tasks, "game-1", "user-1"
        )

        self.assertNotEqual(hash_base, hash_changed)

    def test_different_user_returns_different_hash(self):
        tasks_simulated = [{"externalTaskId": "t1", "points": 10}]

        hash_user_1 = calculate_hash_simulated_strategy(
            tasks_simulated, "game-1", "user-1"
        )
        hash_user_2 = calculate_hash_simulated_strategy(
            tasks_simulated, "game-1", "user-2"
        )

        self.assertNotEqual(hash_user_1, hash_user_2)


if __name__ == "__main__":
    unittest.main()

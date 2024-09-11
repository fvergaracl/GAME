import unittest
from app.util.class_object import singleton


@singleton
class MySingletonClass:
    def __init__(self, value):
        self.value = value


class TestSingleton(unittest.TestCase):
    def setUp(self):
        MySingletonClass._reset_instance()

    def test_single_instance(self):
        """
        Test that only a single instance of the class is created.
        """
        instance1 = MySingletonClass(10)
        instance2 = MySingletonClass(20)

        self.assertIs(instance1, instance2)

        self.assertEqual(instance1.value, 10)
        self.assertEqual(instance2.value, 10)

    def test_singleton_with_arguments(self):
        """
        Test that arguments are only used on the first instantiation.
        """
        instance1 = MySingletonClass(30)
        instance2 = MySingletonClass(40)

        self.assertEqual(instance1.value, 30)
        self.assertEqual(instance2.value, 30)

    def test_singleton_reset_between_tests(self):
        """
        Test that the singleton pattern does not persist across different
          tests.
        """
        @singleton
        class AnotherSingletonClass:
            def __init__(self, value):
                self.value = value

        AnotherSingletonClass._reset_instance()
        first_instance = AnotherSingletonClass(50)
        second_instance = AnotherSingletonClass(60)

        self.assertIs(first_instance, second_instance)

        self.assertEqual(first_instance.value, 50)
        self.assertEqual(second_instance.value, 50)

    def test_singleton_multiple_classes(self):
        """
        Test that singleton works independently for multiple classes.
        """
        @singleton
        class SingletonA:
            def __init__(self, value):
                self.value = value

        @singleton
        class SingletonB:
            def __init__(self, value):
                self.value = value

        SingletonA._reset_instance()
        SingletonB._reset_instance()

        instance_a1 = SingletonA(100)
        instance_a2 = SingletonA(200)
        instance_b1 = SingletonB(300)
        instance_b2 = SingletonB(400)

        # SingletonA instances should be the same
        self.assertIs(instance_a1, instance_a2)
        self.assertEqual(instance_a1.value, 100)
        self.assertEqual(instance_a2.value, 100)

        # SingletonB instances should be the same
        self.assertIs(instance_b1, instance_b2)
        self.assertEqual(instance_b1.value, 300)
        self.assertEqual(instance_b2.value, 300)

        # SingletonA and SingletonB should not interfere with each other
        self.assertIsNot(instance_a1, instance_b1)


if __name__ == "__main__":
    unittest.main()

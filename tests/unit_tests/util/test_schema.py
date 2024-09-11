import unittest
from pydantic import BaseModel
from typing import Optional
from app.util.schema import AllOptional


class TestModel(BaseModel, metaclass=AllOptional):
    id: int
    name: str
    is_active: bool


class TestSchemaMetaclass(unittest.TestCase):

    def test_all_fields_optional(self):
        """
        Test that all fields of the model are optional.
        """
        model = TestModel()
        self.assertIsNone(model.id)
        self.assertIsNone(model.name)
        self.assertIsNone(model.is_active)

    def test_partial_fields(self):
        """
        Test that we can create the model with only some fields.
        """
        model = TestModel(id=1)
        self.assertEqual(model.id, 1)
        self.assertIsNone(model.name)
        self.assertIsNone(model.is_active)

        model = TestModel(name="Test Name")
        self.assertEqual(model.name, "Test Name")
        self.assertIsNone(model.id)
        self.assertIsNone(model.is_active)

    def test_full_fields(self):
        """
        Test that we can create the model with all fields.
        """
        model = TestModel(id=1, name="John", is_active=True)
        self.assertEqual(model.id, 1)
        self.assertEqual(model.name, "John")
        self.assertTrue(model.is_active)

    def test_invalid_field_type(self):
        """
        Test that an invalid field type raises a validation error.
        """
        with self.assertRaises(ValueError):
            TestModel(id="not an int")

        with self.assertRaises(ValueError):
            TestModel(is_active="not a bool")

    def test_annotations_are_optional(self):
        """
        Test that the annotations for all fields are Optional.
        """
        self.assertEqual(TestModel.__annotations__["id"], Optional[int])
        self.assertEqual(TestModel.__annotations__["name"], Optional[str])
        self.assertEqual(TestModel.__annotations__[
                         "is_active"], Optional[bool])


if __name__ == "__main__":
    unittest.main()

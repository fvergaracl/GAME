import unittest
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import and_
from app.util.query_builder import dict_to_sqlalchemy_filter_options

Base = declarative_base()


class TestModel(Base):
    """
    Test model for the query builder tests.
    """
    __tablename__ = 'test_model'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    is_active = Column(Boolean)


# Create an in-memory SQLite database
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


class TestQueryBuilder(unittest.TestCase):
    def test_basic_equality_filter(self):
        """
        Test that the function generates a basic equality filter.
        """
        filter_dict = {"age": 25}
        filter_options = dict_to_sqlalchemy_filter_options(
            TestModel, filter_dict)
        expected_filter = TestModel.age == 25
        self.assertEqual(str(filter_options), str(and_(True, expected_filter)))

    def test_like_string_filter(self):
        """
        Test that the function generates a LIKE filter for strings.
        """
        filter_dict = {"name": "John"}
        filter_options = dict_to_sqlalchemy_filter_options(
            TestModel, filter_dict)
        expected_filter = TestModel.name.like("%John%")
        self.assertEqual(str(filter_options), str(and_(True, expected_filter)))

    def test_boolean_filter(self):
        """
        Test that the function generates a filter for boolean values.
        """
        filter_dict = {"is_active": True}
        filter_options = dict_to_sqlalchemy_filter_options(
            TestModel, filter_dict)
        expected_filter = TestModel.is_active.is_(True)
        self.assertEqual(str(filter_options), str(and_(True, expected_filter)))

    def test_in_filter(self):
        """
        Test that the function generates an IN filter.
        """
        filter_dict = {"age__in": "25,30,35"}
        filter_options = dict_to_sqlalchemy_filter_options(
            TestModel, filter_dict)
        expected_filter = TestModel.age.in_([25, 30, 35])
        self.assertEqual(str(filter_options), str(and_(True, expected_filter)))

    def test_comparison_filters(self):
        """
        Test that the function generates comparison filters.
        """
        filter_dict = {"age__gt": 20, "age__lt": 40}
        filter_options = dict_to_sqlalchemy_filter_options(
            TestModel, filter_dict)
        expected_filter = and_(TestModel.age > 20, TestModel.age < 40)
        self.assertEqual(str(filter_options), str(and_(True, expected_filter)))

    def test_isnull_filter(self):
        """
        Test that the function generates an IS NULL filter.
        """
        filter_dict = {"age__isnull": True}
        filter_options = dict_to_sqlalchemy_filter_options(
            TestModel, filter_dict)
        expected_filter = TestModel.age.__eq__(None)
        self.assertEqual(str(filter_options), str(and_(True, expected_filter)))

    def test_combined_filters(self):
        """
        Test that the function correctly combines multiple filters.
        """
        filter_dict = {
            "age__gt": 20,
            "name": "John",
            "is_active": True,
        }
        filter_options = dict_to_sqlalchemy_filter_options(
            TestModel, filter_dict)

        sql_string = str(filter_options)

        self.assertIn("test_model.age > :age_1", sql_string)
        self.assertIn("test_model.name LIKE", sql_string)
        self.assertIn("test_model.is_active IS true", sql_string)


if __name__ == "__main__":
    unittest.main()

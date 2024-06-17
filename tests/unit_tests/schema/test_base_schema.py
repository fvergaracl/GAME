from datetime import datetime
from uuid import uuid4
from app.schema.base_schema import (
    RootEndpoint, ModelBaseInfo, FindBase, SearchOptions,
    FindResult, FindDateRange, SuccesfullyCreated, Blank
)


def test_root_endpoint():
    """ Test the RootEndpoint model.
    """
    data = {
        "projectName": "Test Project",
        "version": "1.0.0",
        "message": "Welcome to the Test Project API",
        "docs": "http://testproject/docs",
        "redocs": "http://testproject/redocs",
        "commitVersion": "abc123"
    }
    endpoint = RootEndpoint(**data)
    assert endpoint.projectName == data["projectName"]
    assert endpoint.version == data["version"]
    assert endpoint.message == data["message"]
    assert endpoint.docs == data["docs"]
    assert endpoint.redocs == data["redocs"]
    assert endpoint.commitVersion == data["commitVersion"]


def test_model_base_info():
    """
    Test the ModelBaseInfo model.

    The ModelBaseInfo model is used as a base model for all models.

    The model has the following attributes:
    - id (UUID): Unique identifier
    - created_at (datetime): Created date
    - updated_at (datetime): Updated date
    """
    data = {
        "id": uuid4(),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    base_info = ModelBaseInfo(**data)
    assert base_info.id == data["id"]
    assert base_info.created_at == data["created_at"]
    assert base_info.updated_at == data["updated_at"]


def test_find_base():
    """
    Test the FindBase model.

    The FindBase model is used as a base model for search functionality.

    The model has the following attributes:
    - ordering (Optional[str]): Ordering parameter
    - page (Optional[int]): Page number
    - page_size (Optional[Union[int, str]]): Page size
    """
    data = {
        "ordering": "asc",
        "page": 1,
        "page_size": 10
    }
    find_base = FindBase(**data)
    assert find_base.ordering == data["ordering"]
    assert find_base.page == data["page"]
    assert find_base.page_size == data["page_size"]


def test_search_options():
    """
    Test the SearchOptions model.

    The SearchOptions model is used for search options.

    The model has the following attributes:
    - ordering (Optional[str]): Ordering parameter
    - page (Optional[int]): Page number
    - page_size (Optional[Union[int, str]]): Page size
    - total_count (Optional[int]): Total count of results



    """
    data = {
        "ordering": "asc",
        "page": 1,
        "page_size": 10,
        "total_count": 100
    }
    search_options = SearchOptions(**data)
    assert search_options.ordering == data["ordering"]
    assert search_options.page == data["page"]
    assert search_options.page_size == data["page_size"]
    assert search_options.total_count == data["total_count"]


def test_find_result():
    """

    Test the FindResult model.

    The FindResult model is used for search results.

    The model has the following attributes:
    - items (Optional[List]): List of items
    - search_options (Optional[SearchOptions]): Search options


    """
    data = {
        "items": [{"id": uuid4(), "name": "Item 1"},
                  {"id": uuid4(), "name": "Item 2"}],
        "search_options": {
            "ordering": "asc",
            "page": 1,
            "page_size": 10,
            "total_count": 2
        }
    }
    find_result = FindResult(**data)
    assert find_result.items == data["items"]
    assert find_result.search_options.ordering == (
        data["search_options"]["ordering"]
    )
    assert find_result.search_options.page == (
        data["search_options"]["page"]
    )
    assert find_result.search_options.page_size == (
        data["search_options"]["page_size"]
    )
    assert find_result.search_options.total_count == (
        data["search_options"]["total_count"]
    )


def test_find_date_range():
    """
    Test the FindDateRange model.

    The FindDateRange model is used for date range search filters.

    The model has the following attributes:
    - created_at__lt (Optional[datetime]): Less than date
    - created_at__lte (Optional[datetime]): Less than or equal date
    - created_at__gt (Optional[datetime]): Greater than date
    - created_at__gte (Optional[datetime]): Greater than or equal date

    """
    data = {
        "created_at__lt": "2023-01-01",
        "created_at__lte": "2023-01-01",
        "created_at__gt": "2022-01-01",
        "created_at__gte": "2022-01-01"
    }
    date_range = FindDateRange(**data)
    assert date_range.created_at__lt == data["created_at__lt"]
    assert date_range.created_at__lte == data["created_at__lte"]
    assert date_range.created_at__gt == data["created_at__gt"]
    assert date_range.created_at__gte == data["created_at__gte"]


def test_succesfully_created():
    """
    Test the SuccesfullyCreated model.

    The SuccesfullyCreated model is used to return a success message.

    The model has the following attributes:
    - message (str): Success message

    """

    success = SuccesfullyCreated()
    assert success.message == "Successfully created"


def test_blank():
    """
    Test the Blank model.
    """

    blank = Blank()
    assert blank is not None

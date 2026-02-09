from unittest.mock import MagicMock, patch

import pytest

from app.core.database import BaseModel, Database


def test_basemodel_tablename_uses_lowercase_class_name():
    class SampleModel(BaseModel):
        __abstract__ = True

    assert SampleModel.__tablename__ == "samplemodel"


def test_create_database_calls_metadata_create_all_with_engine():
    database = Database("sqlite:///:memory:")

    with patch.object(BaseModel.metadata, "create_all") as mock_create_all:
        database.create_database()

    mock_create_all.assert_called_once_with(database._engine)


def test_session_context_yields_session_and_closes_on_success():
    database = Database("sqlite:///:memory:")
    fake_session = MagicMock()
    database._session_factory = MagicMock(return_value=fake_session)

    with database.session() as session:
        assert session is fake_session

    fake_session.rollback.assert_not_called()
    fake_session.close.assert_called_once()


def test_session_context_rolls_back_and_closes_on_exception():
    database = Database("sqlite:///:memory:")
    fake_session = MagicMock()
    database._session_factory = MagicMock(return_value=fake_session)

    with pytest.raises(RuntimeError, match="boom"):
        with database.session():
            raise RuntimeError("boom")

    fake_session.rollback.assert_called_once()
    fake_session.close.assert_called_once()

from datetime import datetime
from uuid import UUID
from app.model.logs import Logs


def create_logs_instance(
    log_level="info", message="Test message", module="test_module", details=None
):
    if details is None:
        details = {"key": "value"}
    return Logs(
        log_level=log_level,
        message=message,
        module=module,
        details=details,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def test_logs_creation():
    """
    Test the creation of a Logs instance.
    """
    log = create_logs_instance()
    assert isinstance(log, Logs)
    assert isinstance(log.id, UUID)
    assert isinstance(log.created_at, datetime)
    assert isinstance(log.updated_at, datetime)
    assert log.log_level == "info"
    assert log.message == "Test message"
    assert log.module == "test_module"
    assert log.details == {"key": "value"}


def test_logs_str():
    """
    Test the __str__ method of Logs.
    """
    log = create_logs_instance()
    expected_str = (
        f"Logs: (id={log.id}, log_level={log.log_level}, "
        f"message={log.message}, module={log.module}, "
        f"details={log.details}, created_at={log.created_at}, "
        f"updated_at={log.updated_at})"
    )
    assert str(log) == expected_str


def test_logs_repr():
    """
    Test the __repr__ method of Logs.
    """
    log = create_logs_instance()
    expected_repr = (
        f"Logs: (id={log.id}, log_level={log.log_level}, "
        f"message={log.message}, module={log.module}, "
        f"details={log.details}, created_at={log.created_at}, "
        f"updated_at={log.updated_at})"
    )
    assert repr(log) == expected_repr


def test_logs_equality():
    """
    Test the equality operator for Logs.
    """
    log1 = create_logs_instance()
    log2 = create_logs_instance()

    log2.id = log1.id
    log2.created_at = log1.created_at
    log2.updated_at = log1.updated_at
    log2.log_level = log1.log_level
    log2.message = log1.message
    log2.module = log1.module
    log2.details = log1.details

    assert log1 == log2


def test_logs_hash():
    """
    Test the __hash__ method of Logs.
    """
    log = create_logs_instance()
    expected_hash = hash((log.log_level, log.message, log.module, str(log.details)))
    assert hash(log) == expected_hash


def test_logs_log_level():
    """
    Test the log_level field in Logs.
    """
    log = create_logs_instance(log_level="error")
    assert log.log_level == "error"


def test_logs_message():
    """
    Test the message field in Logs.
    """
    log = create_logs_instance(message="New message")
    assert log.message == "New message"


def test_logs_module():
    """
    Test the module field in Logs.
    """
    log = create_logs_instance(module="auth_module")
    assert log.module == "auth_module"


def test_logs_details():
    """
    Test the details field in Logs.
    """
    details = {"event": "login", "status": "success"}
    log = create_logs_instance(details=details)
    assert log.details == details

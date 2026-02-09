from datetime import datetime
from uuid import uuid4

from app.model.api_key import ApiKey
from app.model.api_requests import ApiRequests
from app.model.kpi_metrics import KpiMetrics
from app.model.oauth_users import OAuthUsers
from app.model.uptime_logs import UptimeLogs
from app.model.user_game_config import UserGameConfig
from app.model.user_interactions import UserInteractions


def _api_key():
    return ApiKey(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        apiKey="api-key",
        client="client-a",
        description="desc",
        active=True,
        createdBy="creator",
    )


def _api_request():
    return ApiRequests(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        userId=str(uuid4()),
        endpoint="/health",
        statusCode=200,
        responseTimeMS=33,
        requestType="GET",
    )


def _kpi_metric():
    return KpiMetrics(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        day="2026-02-09",
        totalRequests=10,
        successRate=99,
        avgLatencyMS=120,
        errorRate=1,
        activeUsers=7,
        retentionRate=80,
        avgInteractionsPerUser=5,
    )


def _oauth_user():
    return OAuthUsers(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        provider="keycloak",
        provider_user_id="sub-1",
        status="active",
    )


def _uptime_log():
    return UptimeLogs(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status="up",
    )


def _user_game_config():
    return UserGameConfig(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        userId=str(uuid4()),
        gameId=str(uuid4()),
        experimentGroup="A",
        configData={"difficulty": "normal"},
    )


def _user_interaction():
    return UserInteractions(
        id=str(uuid4()),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        userId=str(uuid4()),
        taskId=str(uuid4()),
        interactionType="task",
        interactionDetail="completed",
    )


def test_api_key_str_repr_and_eq():
    model = _api_key()
    model_copy = _api_key()
    model_copy.apiKey = model.apiKey
    model_copy.description = model.description
    model_copy.active = model.active
    model_copy.createdBy = model.createdBy

    assert "ApiKey: (id=" in str(model)
    assert "ApiKey: (id=" in repr(model)
    assert model == model_copy


def test_api_requests_str_repr_and_eq():
    model = _api_request()
    model_copy = _api_request()
    model_copy.userId = model.userId
    model_copy.endpoint = model.endpoint
    model_copy.statusCode = model.statusCode
    model_copy.responseTimeMS = model.responseTimeMS
    model_copy.requestType = model.requestType

    assert "ApiRequests: (id=" in str(model)
    assert repr(model) == str(model)
    assert model == model_copy


def test_kpi_metrics_str_repr_and_eq():
    model = _kpi_metric()
    model_copy = _kpi_metric()
    model_copy.day = model.day
    model_copy.totalRequests = model.totalRequests
    model_copy.successRate = model.successRate
    model_copy.avgLatencyMS = model.avgLatencyMS
    model_copy.errorRate = model.errorRate
    model_copy.activeUsers = model.activeUsers
    model_copy.retentionRate = model.retentionRate
    model_copy.avgInteractionsPerUser = model.avgInteractionsPerUser

    assert "KpiMetrics: (id=" in str(model)
    assert repr(model) == str(model)
    assert model == model_copy


def test_oauth_users_str_repr_eq_and_hash():
    model = _oauth_user()
    model_copy = _oauth_user()
    model_copy.provider = model.provider
    model_copy.provider_user_id = model.provider_user_id
    model_copy.status = model.status

    assert "OAuthUsers: (id=" in str(model)
    assert "OAuthUsers: (id=" in repr(model)
    assert model == model_copy
    assert hash(model) == hash((model.provider, model.provider_user_id, model.status))


def test_uptime_logs_str_repr_and_eq():
    model = _uptime_log()
    model_copy = _uptime_log()
    model_copy.status = model.status

    assert "UptimeLogs: (id=" in str(model)
    assert repr(model) == str(model)
    assert model == model_copy


def test_user_game_config_str_repr_and_eq():
    model = _user_game_config()
    model_copy = _user_game_config()
    model_copy.id = model.id
    model_copy.userId = model.userId
    model_copy.gameId = model.gameId
    model_copy.experimentGroup = model.experimentGroup
    model_copy.configData = model.configData
    model_copy.created_at = model.created_at
    model_copy.updated_at = model.updated_at

    assert "UserGameConfig: (id=" in str(model)
    assert "UserGameConfig: (id=" in repr(model)
    assert model == model_copy


def test_user_interactions_str_repr_and_eq():
    model = _user_interaction()
    model_copy = _user_interaction()
    model_copy.userId = model.userId
    model_copy.interactionType = model.interactionType
    model_copy.interactionDetail = model.interactionDetail

    assert "UserInteractions: (id=" in str(model)
    assert repr(model) == str(model)
    assert model == model_copy

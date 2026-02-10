import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import httpx
import jwt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.model.api_key import ApiKey
from app.model.logs import Logs
from app.model.oauth_users import OAuthUsers


pytestmark = [
    pytest.mark.e2e_real_http,
    pytest.mark.skipif(
        os.getenv("RUN_REAL_E2E", "0") != "1",
        reason=(
            "Set RUN_REAL_E2E=1 and configure E2E environment variables "
            "to run real HTTP + PostgreSQL end-to-end tests."
        ),
    ),
]


@dataclass(frozen=True)
class RealE2EConfig:
    base_url: str
    database_url: str
    keycloak_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str
    admin_username: str
    admin_password: str


@dataclass(frozen=True)
class ApiKeyCreateE2EContext:
    base_url: str
    admin_bearer_token: str
    admin_subject: str
    bootstrap_api_key: str
    client_prefix: str
    created_oauth_user: bool


def _require_env(name: str, fallback: str | None = None) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        if fallback is None:
            raise KeyError(name)
        return fallback
    return value


def _fetch_keycloak_access_token(
    *,
    keycloak_url: str,
    realm: str,
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
) -> str:
    token_url = f"{keycloak_url.rstrip('/')}/realms/{realm}/protocol/openid-connect/token"
    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
    }
    response = httpx.post(token_url, data=payload, timeout=30.0)
    assert response.status_code == 200, (
        f"Unable to obtain Keycloak token from {token_url}. "
        f"status={response.status_code}, body={response.text}"
    )
    body = response.json()
    access_token = body.get("access_token")
    assert access_token, f"Keycloak token response missing access_token: {body}"
    return access_token


def _decode_subject_without_verification(access_token: str) -> str:
    decoded = jwt.decode(
        access_token,
        options={
            "verify_signature": False,
            "verify_exp": False,
            "verify_aud": False,
        },
    )
    subject = decoded.get("sub")
    assert isinstance(subject, str) and subject.strip(), (
        "Decoded bearer token does not contain a valid `sub` claim."
    )
    return subject


def _post_create_apikey(
    *,
    base_url: str,
    payload: dict,
    bearer_token: str | None,
    x_api_key: str | None,
) -> httpx.Response:
    headers = {"Content-Type": "application/json"}
    if bearer_token is not None:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if x_api_key is not None:
        headers["X-API-Key"] = x_api_key

    return httpx.post(
        f"{base_url.rstrip('/')}/apikey/create",
        headers=headers,
        json=payload,
        timeout=30.0,
    )


def _count_apikeys_by_client(session: Session, client_name: str) -> int:
    return session.query(ApiKey).filter(ApiKey.client == client_name).count()


def _count_apikeys_by_prefix(session: Session, client_prefix: str) -> int:
    return session.query(ApiKey).filter(ApiKey.client.like(f"{client_prefix}%")).count()


def _optional_env(name: str, fallback: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return fallback
    return value


@pytest.fixture(scope="session")
def real_e2e_config() -> RealE2EConfig:
    try:
        database_url = _require_env("E2E_DATABASE_URL", os.getenv("DATABASE_URL"))
        keycloak_url = _require_env(
            "E2E_KEYCLOAK_URL",
            os.getenv("KEYCLOAK_URL", "http://localhost:8080"),
        )
        keycloak_realm = _require_env(
            "E2E_KEYCLOAK_REALM",
            os.getenv("KEYCLOAK_REALM"),
        )
        keycloak_client_id = _require_env(
            "E2E_KEYCLOAK_CLIENT_ID",
            os.getenv("KEYCLOAK_CLIENT_ID"),
        )
        keycloak_client_secret = _require_env(
            "E2E_KEYCLOAK_CLIENT_SECRET",
            os.getenv("KEYCLOAK_CLIENT_SECRET"),
        )
        admin_username = _require_env(
            "E2E_KEYCLOAK_ADMIN_USERNAME",
            os.getenv("KEYCLOAK_ADMIN_USERNAME", "game_admin@example.com"),
        )
        admin_password = _require_env(
            "E2E_KEYCLOAK_ADMIN_PASSWORD",
            os.getenv("KEYCLOAK_USER_WITH_ROLE_PASSWORD"),
        )
    except KeyError as exc:
        missing_name = str(exc).strip("'")
        pytest.fail(
            "RUN_REAL_E2E=1 requires environment variable "
            f"`{missing_name}` (or its documented fallback).",
            pytrace=False,
        )
        raise

    if not database_url.startswith("postgresql"):
        pytest.fail(
            "E2E_DATABASE_URL / DATABASE_URL must point to PostgreSQL "
            f"(received: {database_url})",
            pytrace=False,
        )

    return RealE2EConfig(
        base_url=os.getenv("E2E_BASE_URL", "http://localhost:8000/api/v1"),
        database_url=database_url,
        keycloak_url=keycloak_url,
        keycloak_realm=keycloak_realm,
        keycloak_client_id=keycloak_client_id,
        keycloak_client_secret=keycloak_client_secret,
        admin_username=admin_username,
        admin_password=admin_password,
    )


@pytest.fixture(scope="session")
def postgres_engine(real_e2e_config: RealE2EConfig) -> Engine:
    engine = create_engine(real_e2e_config.database_url, future=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def apikey_create_context(
    real_e2e_config: RealE2EConfig,
    postgres_engine: Engine,
) -> ApiKeyCreateE2EContext:
    admin_bearer_token = _fetch_keycloak_access_token(
        keycloak_url=real_e2e_config.keycloak_url,
        realm=real_e2e_config.keycloak_realm,
        client_id=real_e2e_config.keycloak_client_id,
        client_secret=real_e2e_config.keycloak_client_secret,
        username=real_e2e_config.admin_username,
        password=real_e2e_config.admin_password,
    )
    admin_subject = _decode_subject_without_verification(admin_bearer_token)

    run_id = uuid.uuid4().hex
    client_prefix = f"e2e-apikey-create-{run_id}"
    bootstrap_api_key = f"bootstrap-{run_id}-{uuid.uuid4().hex}"
    bootstrap_client = f"{client_prefix}-bootstrap"

    created_oauth_user = False

    with Session(postgres_engine) as session:
        oauth_user = (
            session.query(OAuthUsers)
            .filter(OAuthUsers.provider_user_id == admin_subject)
            .one_or_none()
        )
        if oauth_user is None:
            session.add(
                OAuthUsers(
                    provider="keycloak",
                    provider_user_id=admin_subject,
                    status="active",
                )
            )
            created_oauth_user = True

        session.add(
            ApiKey(
                apiKey=bootstrap_api_key,
                client=bootstrap_client,
                description="Bootstrap API key for /apikey/create E2E tests",
                active=True,
                createdBy=admin_subject,
                oauth_user_id=admin_subject,
            )
        )
        session.commit()

    try:
        yield ApiKeyCreateE2EContext(
            base_url=real_e2e_config.base_url,
            admin_bearer_token=admin_bearer_token,
            admin_subject=admin_subject,
            bootstrap_api_key=bootstrap_api_key,
            client_prefix=client_prefix,
            created_oauth_user=created_oauth_user,
        )
    finally:
        with Session(postgres_engine) as session:
            session.query(Logs).filter(
                Logs.apiKey_used == bootstrap_api_key
            ).delete(synchronize_session=False)
            session.query(ApiKey).filter(
                ApiKey.client.like(f"{client_prefix}%")
            ).delete(synchronize_session=False)
            if created_oauth_user:
                session.query(OAuthUsers).filter(
                    OAuthUsers.provider_user_id == admin_subject
                ).delete(synchronize_session=False)
            session.commit()


@pytest.fixture
def non_admin_bearer_token(real_e2e_config: RealE2EConfig) -> str:
    username = _optional_env(
        "E2E_KEYCLOAK_NON_ADMIN_USERNAME",
        os.getenv("KEYCLOAK_USER_NO_ROLE_USERNAME", "game_user@example.com"),
    )
    password = _optional_env(
        "E2E_KEYCLOAK_NON_ADMIN_PASSWORD",
        os.getenv("KEYCLOAK_USER_NO_ROLE_PASSWORD"),
    )
    if not username or not password:
        pytest.skip(
            "Set E2E_KEYCLOAK_NON_ADMIN_USERNAME and "
            "E2E_KEYCLOAK_NON_ADMIN_PASSWORD to validate role-based rejection."
        )

    return _fetch_keycloak_access_token(
        keycloak_url=real_e2e_config.keycloak_url,
        realm=real_e2e_config.keycloak_realm,
        client_id=real_e2e_config.keycloak_client_id,
        client_secret=real_e2e_config.keycloak_client_secret,
        username=username,
        password=password,
    )


def test_apikey_create_happy_path(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
):
    payload = {
        "client": f"{apikey_create_context.client_prefix}-happy",
        "description": "Happy path creation from E2E test",
    }
    with Session(postgres_engine) as session:
        before_count = _count_apikeys_by_client(session, payload["client"])

    response = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=payload,
        bearer_token=apikey_create_context.admin_bearer_token,
        x_api_key=apikey_create_context.bootstrap_api_key,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["client"] == payload["client"]
    assert body["description"] == payload["description"]
    assert body["createdBy"] == apikey_create_context.admin_subject
    assert body["message"] == "API Key created successfully"
    assert isinstance(body["apiKey"], str) and body["apiKey"].strip() != ""

    with Session(postgres_engine) as session:
        after_count = _count_apikeys_by_client(session, payload["client"])
        assert after_count == before_count + 1

        created = (
            session.query(ApiKey).filter(ApiKey.apiKey == body["apiKey"]).one_or_none()
        )
        assert created is not None
        assert created.client == payload["client"]
        assert created.description == payload["description"]
        assert created.createdBy == apikey_create_context.admin_subject
        assert created.active is True


def test_apikey_create_invalid_input_does_not_change_state(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
):
    invalid_payload = {
        "client": f"{apikey_create_context.client_prefix}-invalid-input",
        # Missing required "description"
    }
    with Session(postgres_engine) as session:
        before_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )

    response = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=invalid_payload,
        bearer_token=apikey_create_context.admin_bearer_token,
        x_api_key=apikey_create_context.bootstrap_api_key,
    )

    assert response.status_code == 422, response.text

    with Session(postgres_engine) as session:
        after_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )
        assert after_count == before_count


def test_apikey_create_missing_bearer_rejected_without_side_effects(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
):
    payload = {
        "client": f"{apikey_create_context.client_prefix}-missing-bearer",
        "description": "Auth failure scenario without bearer token",
    }
    with Session(postgres_engine) as session:
        before_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )

    response = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=payload,
        bearer_token=None,
        x_api_key=apikey_create_context.bootstrap_api_key,
    )

    assert response.status_code == 401, response.text

    with Session(postgres_engine) as session:
        after_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )
        assert after_count == before_count


def test_apikey_create_invalid_bearer_rejected_without_side_effects(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
):
    payload = {
        "client": f"{apikey_create_context.client_prefix}-invalid-bearer",
        "description": "Auth failure scenario with malformed bearer token",
    }
    with Session(postgres_engine) as session:
        before_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )

    response = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=payload,
        bearer_token="malformed.jwt.token",
        x_api_key=apikey_create_context.bootstrap_api_key,
    )

    assert response.status_code == 401, response.text

    with Session(postgres_engine) as session:
        after_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )
        assert after_count == before_count


def test_apikey_create_invalid_api_key_rejected_without_side_effects(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
):
    payload = {
        "client": f"{apikey_create_context.client_prefix}-invalid-api-key",
        "description": "Auth failure scenario with invalid X-API-Key",
    }
    with Session(postgres_engine) as session:
        before_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )

    response = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=payload,
        bearer_token=apikey_create_context.admin_bearer_token,
        x_api_key=f"invalid-{uuid.uuid4().hex}",
    )

    assert response.status_code == 403, response.text

    with Session(postgres_engine) as session:
        after_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )
        assert after_count == before_count


def test_apikey_create_non_admin_role_forbidden_without_side_effects(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
    non_admin_bearer_token: str,
):
    payload = {
        "client": f"{apikey_create_context.client_prefix}-non-admin-role",
        "description": "Authorization failure for non-admin role",
    }
    with Session(postgres_engine) as session:
        before_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )

    response = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=payload,
        bearer_token=non_admin_bearer_token,
        x_api_key=apikey_create_context.bootstrap_api_key,
    )

    assert response.status_code == 403, response.text

    with Session(postgres_engine) as session:
        after_count = _count_apikeys_by_prefix(
            session, apikey_create_context.client_prefix
        )
        assert after_count == before_count


def test_apikey_create_retry_same_payload_is_consistent(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
):
    payload = {
        "client": f"{apikey_create_context.client_prefix}-retry",
        "description": "Retry scenario with same payload",
    }

    response_1 = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=payload,
        bearer_token=apikey_create_context.admin_bearer_token,
        x_api_key=apikey_create_context.bootstrap_api_key,
    )
    response_2 = _post_create_apikey(
        base_url=apikey_create_context.base_url,
        payload=payload,
        bearer_token=apikey_create_context.admin_bearer_token,
        x_api_key=apikey_create_context.bootstrap_api_key,
    )

    assert response_1.status_code == 201, response_1.text
    assert response_2.status_code == 201, response_2.text

    body_1 = response_1.json()
    body_2 = response_2.json()
    assert body_1["apiKey"] != body_2["apiKey"]

    with Session(postgres_engine) as session:
        created_rows = (
            session.query(ApiKey).filter(ApiKey.client == payload["client"]).all()
        )
        assert len(created_rows) == 2
        assert {row.apiKey for row in created_rows} == {
            body_1["apiKey"],
            body_2["apiKey"],
        }
        assert all(
            row.createdBy == apikey_create_context.admin_subject
            for row in created_rows
        )


def test_apikey_create_concurrent_requests_are_transactionally_safe(
    apikey_create_context: ApiKeyCreateE2EContext,
    postgres_engine: Engine,
):
    request_count = 8
    payloads = [
        {
            "client": f"{apikey_create_context.client_prefix}-concurrent-{index}",
            "description": f"Concurrent request #{index}",
        }
        for index in range(request_count)
    ]

    def _worker(payload: dict) -> httpx.Response:
        return _post_create_apikey(
            base_url=apikey_create_context.base_url,
            payload=payload,
            bearer_token=apikey_create_context.admin_bearer_token,
            x_api_key=apikey_create_context.bootstrap_api_key,
        )

    with ThreadPoolExecutor(max_workers=request_count) as executor:
        responses = list(executor.map(_worker, payloads))

    status_codes = [response.status_code for response in responses]
    response_bodies = [response.text for response in responses]
    assert all(code == 201 for code in status_codes), (
        f"Unexpected status codes in concurrent run: {status_codes}. "
        f"bodies={response_bodies}"
    )

    response_jsons = [response.json() for response in responses]
    returned_api_keys = [body["apiKey"] for body in response_jsons]
    assert len(returned_api_keys) == request_count
    assert len(set(returned_api_keys)) == request_count

    created_clients = [payload["client"] for payload in payloads]
    with Session(postgres_engine) as session:
        created_rows = (
            session.query(ApiKey).filter(ApiKey.client.in_(created_clients)).all()
        )
        assert len(created_rows) == request_count
        assert {row.client for row in created_rows} == set(created_clients)
        assert len({row.apiKey for row in created_rows}) == request_count

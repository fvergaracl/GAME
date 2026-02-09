from unittest.mock import patch

from app import main as main_module


def test_custom_openapi_adds_extra_server_and_rewrites_v1_paths(monkeypatch):
    previous_openapi_schema = main_module.app.openapi_schema

    def fake_get_openapi(**kwargs):
        return {
            "servers": kwargs["servers"],
            "paths": {
                "/api/v1/health": {"get": {"summary": "Health"}},
                "/keep": {"get": {"summary": "Keep"}},
            },
        }

    monkeypatch.setattr(main_module, "get_openapi", fake_get_openapi)
    monkeypatch.setattr(main_module.configs, "EXTRA_SERVER_URL", "https://extra.example")
    monkeypatch.setattr(main_module.configs, "EXTRA_SERVER_DESCRIPTION", "Extra server")
    main_module.app.openapi_schema = None

    try:
        schema = main_module.custom_openapi()
    finally:
        main_module.app.openapi_schema = previous_openapi_schema

    assert {"url": "https://extra.example", "description": "Extra server"} in schema[
        "servers"
    ]
    assert "/health" in schema["paths"]
    assert "/api/v1/health" not in schema["paths"]


def test_custom_openapi_returns_cached_schema_when_available():
    previous_openapi_schema = main_module.app.openapi_schema
    cached_schema = {"cached": True}
    main_module.app.openapi_schema = cached_schema

    try:
        result = main_module.custom_openapi()
    finally:
        main_module.app.openapi_schema = previous_openapi_schema

    assert result is cached_schema


def test_get_git_commit_hash_returns_unknown_on_failure():
    with patch("app.main.subprocess.check_output", side_effect=RuntimeError("fail")):
        result = main_module.get_git_commit_hash()

    assert result == "unknown"


def test_root_route_endpoint_returns_redirect_response():
    root_route = next(route for route in main_module.app.routes if route.path == "/")

    response = root_route.endpoint()

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_app_creator_initializes_sentry_when_dsn_is_set(monkeypatch):
    monkeypatch.setattr(main_module.configs, "SENTRY_DSN", "https://dsn.example")
    monkeypatch.setattr(main_module.configs, "SENTRY_ENVIRONMENT", "test")
    monkeypatch.setattr(main_module.configs, "SENTRY_RELEASE", "1.2.3")

    try:
        main_module.AppCreator._reset_instance()
        with patch("app.main.sentry_sdk.init") as mock_sentry_init:
            main_module.AppCreator()
        mock_sentry_init.assert_called_once()
    finally:
        main_module.AppCreator._reset_instance()

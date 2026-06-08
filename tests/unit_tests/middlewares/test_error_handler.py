"""
Tests for ``CatchUnhandledErrorsMiddleware``.

The middleware exists so that unhandled 500s keep their CORS headers (a raw
Starlette 500 is rendered by ``ServerErrorMiddleware``, which sits *outside*
``CORSMiddleware``, so the browser blocks it and the dashboard shows a bare
"Network Error"). These tests build a tiny app with the same middleware
ordering used in ``app/main.py`` (CORS added last → outermost) and assert the
header survives a 500.
"""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware

from app.middlewares.error_handler import CatchUnhandledErrorsMiddleware

ORIGIN = "http://localhost:3000"


def _build_app(*, with_catch_all: bool) -> FastAPI:
    app = FastAPI()
    # Mirror main.py ordering: the catch-all is added first so the CORS layer
    # added afterwards stays outermost and wraps it.
    if with_catch_all:
        app.add_middleware(CatchUnhandledErrorsMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/boom")
    def boom():
        raise ValueError("kaboom")

    @app.get("/http-error")
    def http_error():
        raise HTTPException(status_code=400, detail="nope")

    @app.get("/ok")
    def ok():
        return {"ok": True}

    return app


def test_unhandled_500_keeps_cors_header_and_json_body():
    client = TestClient(_build_app(with_catch_all=True), raise_server_exceptions=False)

    resp = client.get("/boom", headers={"Origin": ORIGIN})

    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error"}
    assert resp.headers["access-control-allow-origin"] == ORIGIN


def test_without_middleware_500_loses_cors_header():
    """Control: this is the bug the middleware fixes — a raw 500 has no
    ``access-control-allow-origin`` header, so the browser reports a generic
    network failure instead of the real status."""
    client = TestClient(_build_app(with_catch_all=False), raise_server_exceptions=False)

    resp = client.get("/boom", headers={"Origin": ORIGIN})

    assert resp.status_code == 500
    assert "access-control-allow-origin" not in resp.headers


def test_http_exception_still_maps_to_4xx_with_cors():
    """The catch-all must not swallow ``HTTPException`` — those are handled by
    Starlette's ExceptionMiddleware (inside CORS) and keep their status."""
    client = TestClient(_build_app(with_catch_all=True), raise_server_exceptions=False)

    resp = client.get("/http-error", headers={"Origin": ORIGIN})

    assert resp.status_code == 400
    assert resp.json() == {"detail": "nope"}
    assert resp.headers["access-control-allow-origin"] == ORIGIN


def test_successful_request_is_untouched():
    client = TestClient(_build_app(with_catch_all=True))

    resp = client.get("/ok", headers={"Origin": ORIGIN})

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert resp.headers["access-control-allow-origin"] == ORIGIN

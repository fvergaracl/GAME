import os

from fastapi.testclient import TestClient

os.environ["SENTRY_DSN"] = ""

from app.main import app


def test_root_redirects_to_docs_e2e():
    client = TestClient(app)

    response = client.get("/", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/docs"


def test_docs_is_available_e2e():
    client = TestClient(app)

    response = client.get("/docs")

    assert response.status_code == 200

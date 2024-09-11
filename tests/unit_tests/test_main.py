import unittest
from fastapi.testclient import TestClient
from app.main import app, get_git_commit_hash, get_project_data, AppCreator


class TestMain(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_redirect(self):
        """
        Test if the root path ("/") redirects to the /docs endpoint.
        """
        response = self.client.get("/")
        assert response.status_code in [200, 307]
        if response.status_code == 307:
            assert response.headers["location"] == "/docs"

    def test_docs_url(self):
        """
        Test if the /docs endpoint is accessible.
        """
        response = self.client.get("/docs")
        assert response.status_code == 200
        assert "Swagger UI" in response.text

    def test_custom_openapi(self):
        """
        Test the custom OpenAPI schema generation.
        """
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        openapi_json = response.json()
        assert "paths" in openapi_json
        assert "info" in openapi_json
        assert openapi_json["info"]["title"] == get_project_data()["name"]

    def test_git_commit_hash(self):
        """
        Test the git commit hash function.
        """
        commit_hash = get_git_commit_hash()
        assert isinstance(commit_hash, str)
        assert len(commit_hash) > 0

    def test_app_creator_singleton(self):
        """
        Test that AppCreator behaves as a singleton.
        """
        app_creator_instance_1 = AppCreator()
        app_creator_instance_2 = AppCreator()
        assert app_creator_instance_1 is app_creator_instance_2

    def test_cors_middleware(self):
        """
        Test if CORS middleware is properly configured.
        """
        response = self.client.options("/api/v1/some-endpoint", headers={
            "Origin": "http://localhost",
            "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == (
            "http://localhost"
        )


if __name__ == "__main__":
    unittest.main()

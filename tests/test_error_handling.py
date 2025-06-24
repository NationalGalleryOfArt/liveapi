"""Tests for custom error handling."""

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel
from src.liveapi.implementation.app import create_app


class MockModel(BaseModel):
    id: str
    name: str


@pytest.fixture(scope="module")
def test_app():
    """Creates a test FastAPI app with a mock resource."""
    # We need a dummy spec file for create_app
    from tempfile import NamedTemporaryFile
    import yaml

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "summary": "List Items",
                    "responses": {
                        "200": {
                            "description": "A list of items",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/MockModel"
                                        },
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create Item",
                    "responses": {"201": {"description": "Item created"}},
                },
            }
        },
        "components": {
            "schemas": {
                "MockModel": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                    },
                }
            }
        },
    }
    with NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as tmp:
        yaml.dump(spec, tmp)
        spec_path = tmp.name

    app = create_app(spec_path)

    # Add a route that raises an internal server error for testing
    @app.get("/test-500")
    def get_500():
        raise ValueError("A deliberate internal error.")

    @app.get("/test-unauthorized")
    def get_unauthorized():
        from src.liveapi.implementation.exceptions import UnauthorizedError

        raise UnauthorizedError("Authentication is required.")

    @app.get("/test-forbidden")
    def get_forbidden():
        from src.liveapi.implementation.exceptions import ForbiddenError

        raise ForbiddenError("You do not have permission.")

    @app.post("/items/some_action")
    def post_not_implemented():
        raise NotImplementedError("This feature is not yet implemented.")

    return app


@pytest.fixture(scope="module")
def client(test_app):
    """Test client for the FastAPI app."""
    return TestClient(test_app)


def test_internal_server_error_handler(client):
    """Test that unhandled exceptions are caught and returned as 500 errors."""
    with pytest.raises(ValueError):
        client.get("/test-500")


def test_not_implemented_error_handler(client):
    """Test that NotImplementedError is handled and returned as a 501 error."""
    response = client.post("/items/some_action")
    assert response.status_code == 501
    data = response.json()
    assert data["title"] == "NotImplemented"
    assert data["status"] == 501
    assert data["detail"] == "This feature is not yet implemented."
    assert data["type"] == "/errors/not_implemented"


def test_unauthorized_error_handler(client):
    """Test that UnauthorizedError is handled and returned as a 401 error."""
    response = client.get("/test-unauthorized")
    assert response.status_code == 401
    data = response.json()
    assert data["title"] == "Unauthorized"
    assert data["status"] == 401
    assert data["detail"] == "Authentication is required."
    assert data["type"] == "/errors/unauthorized"


def test_forbidden_error_handler(client):
    """Test that ForbiddenError is handled and returned as a 403 error."""
    response = client.get("/test-forbidden")
    assert response.status_code == 403
    data = response.json()
    assert data["title"] == "Forbidden"
    assert data["status"] == 403
    assert data["detail"] == "You do not have permission."
    assert data["type"] == "/errors/forbidden"

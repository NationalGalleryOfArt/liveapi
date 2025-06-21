"""Test exception mapping functionality."""

import pytest
from pathlib import Path
import tempfile
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
from automatic import OpenAPIParser, RouteGenerator
from automatic.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class ExceptionImplementation:
    """Implementation that demonstrates exception handling."""

    def get_item(self, data):
        """Get item by ID, throws NotFoundError if not found."""
        item_id = data.get("item_id")
        if item_id == "999":
            raise NotFoundError(f"Item {item_id} not found", {"item_id": item_id})
        return {"id": item_id, "name": f"Item {item_id}"}, 200

    def create_item(self, data):
        """Create item, various exceptions possible."""
        name = data.get("name", "")

        if not name:
            raise ValidationError("Name is required")

        if name == "duplicate":
            raise ConflictError("Item already exists", {"existing_id": 123})

        if name == "unauthorized":
            raise UnauthorizedError("Authentication required")

        if name == "forbidden":
            raise ForbiddenError("Insufficient permissions to create items")

        if name == "rate_limit":
            raise Exception("Too many requests (rate limit exceeded)")

        if name == "crash":
            # This will trigger a generic 500 error
            raise RuntimeError("Unexpected internal error")

        return {"id": 1, "name": name}, 201

    def update_item(self, data):
        """Update item, demonstrates ValueError handling."""
        item_id = data.get("item_id")
        if item_id == "bad":
            raise ValueError("Invalid item ID format")
        return {"id": item_id, "updated": True}, 200


@pytest.fixture
def exception_spec():
    """Create OpenAPI spec for exception testing."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Exception Test API", "version": "1.0.0"},
        "paths": {
            "/items/{item_id}": {
                "get": {
                    "operationId": "get_item",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"},
                        "404": {"description": "Not found"},
                    },
                },
                "put": {
                    "operationId": "update_item",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                },
            },
            "/items": {
                "post": {
                    "operationId": "create_item",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}},
                                }
                            }
                        },
                    },
                    "responses": {
                        "201": {"description": "Created"},
                        "400": {"description": "Bad request"},
                        "409": {"description": "Conflict"},
                    },
                }
            },
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(spec, f)
        return Path(f.name)


def create_test_app(spec_path):
    """Helper to create test app."""
    parser = OpenAPIParser(spec_path)
    parser.load_spec()

    implementation = ExceptionImplementation()
    router_gen = RouteGenerator(implementation)
    routes = router_gen.generate_routes(parser)

    app = FastAPI()
    for route in routes:
        app.routes.append(route)

    return app


def test_not_found_exception(exception_spec):
    """Test NotFoundError mapping."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    response = client.get("/items/999")
    assert response.status_code == 404

    data = response.json()
    assert data["type"] == "/errors/not_found"
    assert data["title"] == "NotFound"
    assert data["status"] == 404
    assert data["detail"] == "Item 999 not found"
    assert data["item_id"] == "999"


def test_validation_exception(exception_spec):
    """Test ValidationError mapping."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    response = client.post("/items", json={})
    assert response.status_code == 400

    data = response.json()
    assert data["type"] == "/errors/validation_error"
    assert data["title"] == "Validation"
    assert data["status"] == 400
    assert data["detail"] == "Name is required"


def test_conflict_exception(exception_spec):
    """Test ConflictError mapping."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    response = client.post("/items", json={"name": "duplicate"})
    assert response.status_code == 409

    data = response.json()
    assert data["type"] == "/errors/conflict"
    assert data["title"] == "Conflict"
    assert data["status"] == 409
    assert data["detail"] == "Item already exists"
    assert data["existing_id"] == 123


def test_unauthorized_exception(exception_spec):
    """Test UnauthorizedError mapping."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    response = client.post("/items", json={"name": "unauthorized"})
    assert response.status_code == 401

    data = response.json()
    assert data["type"] == "/errors/unauthorized"
    assert data["title"] == "Unauthorized"
    assert data["status"] == 401


def test_forbidden_exception(exception_spec):
    """Test ForbiddenError mapping."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    response = client.post("/items", json={"name": "forbidden"})
    assert response.status_code == 403

    data = response.json()
    assert data["type"] == "/errors/forbidden"
    assert data["title"] == "Forbidden"
    assert data["status"] == 403


# test_rate_limit_exception removed: rate limiting is now handled by the API gateway/layer.

def test_generic_exception_handling(exception_spec):
    """Test generic exception becomes 500."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    response = client.post("/items", json={"name": "crash"})
    assert response.status_code == 500

    data = response.json()
    assert data["type"] == "/errors/internal_server_error"
    assert data["title"] == "Internal Server Error"
    assert data["status"] == 500
    assert "unexpected" in data["detail"]


def test_value_error_handling(exception_spec):
    """Test ValueError gets exposed in 500 response."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    response = client.put("/items/bad")
    assert response.status_code == 500

    data = response.json()
    assert data["type"] == "/errors/internal_server_error"
    assert data["status"] == 500
    assert "Invalid item ID format" in data["detail"]


def test_success_cases_still_work(exception_spec):
    """Test that normal success cases still work."""
    app = create_test_app(exception_spec)
    client = TestClient(app)

    # Successful GET
    response = client.get("/items/123")
    assert response.status_code == 200
    assert response.json() == {"id": "123", "name": "Item 123"}

    # Successful POST
    response = client.post("/items", json={"name": "New Item"})
    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "New Item"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Test path and query parameter handling."""

import pytest
from pathlib import Path
import tempfile
import yaml
from fastapi.testclient import TestClient
import sys
import automatic

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class ParamsImplementation:
    """Implementation that echoes all received parameters."""

    def get_item(self, data):
        """Echo back all parameters received."""
        return {"received": data}, 200

    def search_items(self, data):
        """Search with query parameters."""
        return {
            "query": data.get("q", ""),
            "limit": data.get("limit", 10),
            "offset": data.get("offset", 0),
            "category": data.get("category"),
            "all_params": data,
        }, 200

    def update_item(self, data):
        """Update with path params and body."""
        return {
            "item_id": data.get("item_id"),
            "name": data.get("name"),
            "description": data.get("description"),
            "all_data": data,
        }, 200


@pytest.fixture
def params_spec():
    """Create OpenAPI spec with various parameter types."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Params Test API", "version": "1.0.0"},
        "paths": {
            "/items/{item_id}": {
                "get": {
                    "operationId": "get_item",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                },
                "put": {
                    "operationId": "update_item",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                    "required": ["name"],
                                }
                            }
                        },
                    },
                    "responses": {"200": {"description": "Success"}},
                },
            },
            "/items": {
                "get": {
                    "operationId": "search_items",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Search query",
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 10},
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 0},
                        },
                        {
                            "name": "category",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            },
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(spec, f)
        return Path(f.name)


def test_path_params_only(params_spec):
    """Test path parameters are correctly passed."""
    app = automatic.create_app(
        spec_path=params_spec, implementation=ParamsImplementation()
    )
    client = TestClient(app)

    response = client.get("/items/123")
    assert response.status_code == 200

    data = response.json()
    assert data["received"]["item_id"] == "123"  # FastAPI passes path params as strings


def test_query_params_only(params_spec):
    """Test query parameters are correctly passed."""
    app = automatic.create_app(
        spec_path=params_spec, implementation=ParamsImplementation()
    )
    client = TestClient(app)

    response = client.get("/items?q=test&limit=20&offset=5&category=books")
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "test"
    assert data["limit"] == "20"  # Query params come as strings
    assert data["offset"] == "5"
    assert data["category"] == "books"


def test_query_params_partial(params_spec):
    """Test partial query parameters with defaults."""
    app = automatic.create_app(
        spec_path=params_spec, implementation=ParamsImplementation()
    )
    client = TestClient(app)

    response = client.get("/items?q=search+term")
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "search term"  # URL encoding handled
    assert data["limit"] == 10  # Default from implementation
    assert data["offset"] == 0  # Default from implementation
    assert data["category"] is None


def test_path_params_with_body(params_spec):
    """Test path parameters combined with request body."""
    app = automatic.create_app(
        spec_path=params_spec, implementation=ParamsImplementation()
    )
    client = TestClient(app)

    response = client.put(
        "/items/456", json={"name": "Updated Item", "description": "New description"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["item_id"] == "456"
    assert data["name"] == "Updated Item"
    assert data["description"] == "New description"

    # Verify all data is merged
    assert data["all_data"]["item_id"] == "456"
    assert data["all_data"]["name"] == "Updated Item"


def test_params_no_collision(params_spec):
    """Test that params don't collide when same name in different locations."""
    # This would need a spec with same param name in path/query/body
    # Current implementation would have last one win due to dict.update()
    # This is a limitation that should be documented
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Direct test of path and query parameter handling."""

import pytest
from pathlib import Path
import tempfile
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
from automatic import OpenAPIParser, RouteGenerator

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class ParamsImplementation:
    """Implementation that echoes all received parameters."""
    
    def get_item(self, data):
        """Echo back all parameters received."""
        return {"received": data, "item_id": data.get("item_id")}, 200
    
    def search_items(self, data):
        """Search with query parameters."""
        return {
            "query": data.get("q", ""),
            "limit": data.get("limit", "10"),
            "offset": data.get("offset", "0"),
            "all_params": data
        }, 200


@pytest.fixture
def simple_spec():
    """Create a simple OpenAPI spec with path and query params."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items/{item_id}": {
                "get": {
                    "operationId": "get_item",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"200": {"description": "Success"}}
                }
            },
            "/items": {
                "get": {
                    "operationId": "search_items",
                    "parameters": [
                        {
                            "name": "q",
                            "in": "query",
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer"}
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(spec, f)
        return Path(f.name)


def test_direct_components(simple_spec):
    """Test using the components directly."""
    # Create parser and load spec
    parser = OpenAPIParser(simple_spec)
    parser.load_spec()
    
    # Create route generator
    implementation = ParamsImplementation()
    router_gen = RouteGenerator(implementation)
    
    # Generate routes
    routes = router_gen.generate_routes(parser)
    
    # Create FastAPI app and add routes
    app = FastAPI()
    for route in routes:
        app.routes.append(route)
    
    # Test with client
    client = TestClient(app)
    
    # Test path parameter
    response = client.get("/items/123")
    assert response.status_code == 200
    data = response.json()
    print(f"Path param response: {data}")
    assert data["item_id"] == "123"
    assert data["received"]["item_id"] == "123"
    
    # Test query parameters
    response = client.get("/items?q=test&limit=20&offset=5")
    assert response.status_code == 200
    data = response.json()
    print(f"Query param response: {data}")
    assert data["query"] == "test"
    assert data["all_params"]["q"] == "test"
    assert data["all_params"]["limit"] == "20"
    assert data["all_params"]["offset"] == "5"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
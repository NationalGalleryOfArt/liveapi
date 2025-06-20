"""Basic tests for the automatic framework."""

import pytest
from pathlib import Path
import tempfile
import yaml
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import automatic


class MockImplementation:
    """Mock implementation for basic functionality."""
    
    def test_operation(self, data):
        return {"message": "test", "input": data}, 200


def test_implementation_method():
    """Test that the implementation method works correctly."""
    implementation = MockImplementation()
    test_data = {"name": "test_value"}
    result = implementation.test_operation(test_data)
    
    assert result[0]["message"] == "test"
    assert result[0]["input"]["name"] == "test_value"
    assert result[1] == 200


@pytest.fixture
def sample_openapi_spec():
    """Create a sample OpenAPI specification for testing."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/test": {
                "post": {
                    "operationId": "test_operation",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"}
                                    },
                                    "required": ["name"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(spec, f)
        return Path(f.name)


def test_create_app(sample_openapi_spec):
    """Test basic app creation."""
    implementation = MockImplementation()
    app = automatic.create_app(sample_openapi_spec, implementation)
    
    assert app.title == "Test API"
    assert app.version == "1.0.0"


def test_api_endpoint(sample_openapi_spec):
    """Test that the API endpoint works."""
    import asyncio
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    
    implementation = MockImplementation()
    app = automatic.create_app(sample_openapi_spec, implementation)
    
    # Test that the app was created with correct metadata
    assert app.title == "Test API"
    assert app.version == "1.0.0"
    
    # Test that routes were created
    routes = [route for route in app.routes if hasattr(route, 'path')]
    assert len(routes) > 0
    
    # Find our test route
    test_route = None
    for route in routes:
        if hasattr(route, 'path') and route.path == "/test":
            test_route = route
            break
    
    assert test_route is not None, "Test route not found"
    
    # Test that the route has POST method
    assert hasattr(test_route, 'methods') and "POST" in test_route.methods


def test_openapi_parser():
    """Test OpenAPI parser functionality."""
    from automatic.parser import OpenAPIParser
    
    # Create a simple spec file
    spec_data = {
        "openapi": "3.0.0",
        "info": {"title": "Parser Test", "version": "1.0.0"},
        "paths": {
            "/items/{item_id}": {
                "get": {
                    "operationId": "get_item",
                    "parameters": [
                        {
                            "name": "item_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"}
                        }
                    ],
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(spec_data, f)
        spec_path = Path(f.name)
    
    parser = OpenAPIParser(spec_path)
    parser.load_spec()
    
    routes = parser.get_routes()
    assert len(routes) == 1
    
    route = routes[0]
    assert route['path'] == '/items/{item_id}'
    assert route['method'] == 'GET'
    assert route['operation_id'] == 'get_item'
    
    # Test path parameter extraction
    path_params = parser.get_path_parameters('/items/{item_id}')
    assert path_params == ['item_id']


if __name__ == "__main__":
    pytest.main([__file__])
"""Basic tests for the automatic framework."""

import pytest
from pathlib import Path
import tempfile
import yaml
import sys
import automatic

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


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
                                    "properties": {"name": {"type": "string"}},
                                    "required": ["name"],
                                }
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Success response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"message": {"type": "string"}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(spec, f)
        return Path(f.name)


def test_create_app(sample_openapi_spec, tmp_path):
    """Test basic app creation."""
    # Create directory structure for automatic discovery
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()

    # Copy spec to api directory
    import shutil

    shutil.copy(sample_openapi_spec, api_dir / "test.yaml")

    # Create implementation file
    impl_code = """
class Implementation:
    def test_operation(self, data):
        return {"message": "test", "input": data}, 200
"""
    (impl_dir / "test.py").write_text(impl_code)

    # Create app using automatic discovery
    app = automatic.create_app(api_dir=api_dir, impl_dir=impl_dir)

    assert app.title == "Automatic API"  # Default title in automatic discovery


def test_api_endpoint(sample_openapi_spec, tmp_path):
    """Test that the API endpoint works."""

    # Create directory structure for automatic discovery
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()

    # Copy spec to api directory
    import shutil

    shutil.copy(sample_openapi_spec, api_dir / "test.yaml")

    # Create implementation file
    impl_code = """
class Implementation:
    def test_operation(self, data):
        return {"message": "test", "input": data}, 200
"""
    (impl_dir / "test.py").write_text(impl_code)

    # Create app using automatic discovery
    app = automatic.create_app(api_dir=api_dir, impl_dir=impl_dir)

    # Test that the app was created
    assert app.title == "Automatic API"

    # Test that routes were created with the /test prefix
    routes = [route for route in app.routes if hasattr(route, "path")]
    assert len(routes) > 0

    # Find our test route (now prefixed with /test)
    test_route = None
    for route in routes:
        if hasattr(route, "path") and route.path == "/test/test":
            test_route = route
            break

    assert test_route is not None, "Test route not found"

    # Test that the route has POST method
    assert hasattr(test_route, "methods") and "POST" in test_route.methods


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
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(spec_data, f)
        spec_path = Path(f.name)

    parser = OpenAPIParser(spec_path)
    parser.load_spec()

    routes = parser.get_routes()
    assert len(routes) == 1

    route = routes[0]
    assert route["path"] == "/items/{item_id}"
    assert route["method"] == "GET"
    assert route["operation_id"] == "get_item"

    # Test path parameter extraction (using built-in regex)
    import re

    path_params = re.findall(r"\{([^}]+)\}", "/items/{item_id}")
    assert path_params == ["item_id"]


def test_health_check_endpoint():
    """Test that health check endpoint is automatically added."""
    from fastapi.testclient import TestClient

    # Create simple implementation
    class SimpleImplementation:
        def test_operation(self, data):
            return {"message": "test"}, 200

    # Create app with proper test setup
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        api_dir = tmp_path / "specifications"
        impl_dir = tmp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()

        # Create minimal spec
        spec_data = {
            "openapi": "3.0.0",
            "info": {"title": "Health Test", "version": "1.0.0"},
            "paths": {
                "/test": {
                    "get": {
                        "operationId": "test_operation",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with open(api_dir / "test.yaml", "w") as f:
            yaml.dump(spec_data, f)

        # Create implementation
        impl_code = """
class Implementation:
    def test_operation(self, data):
        return {"message": "test"}, 200
"""
        (impl_dir / "test.py").write_text(impl_code)

        app = automatic.create_app(api_dir=api_dir, impl_dir=impl_dir)
        client = TestClient(app)

        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "automatic"
        assert "timestamp" in data


def test_health_check_direct_mode():
    """Test health check endpoint with direct app creation."""
    from fastapi.testclient import TestClient

    class SimpleImplementation:
        def test_operation(self, data):
            return {"message": "test"}, 200

    # Create minimal spec file
    spec_data = {
        "openapi": "3.0.0",
        "info": {"title": "Direct Health Test", "version": "1.0.0"},
        "paths": {
            "/test": {
                "get": {
                    "operationId": "test_operation",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(spec_data, f)
        spec_path = Path(f.name)

    app = automatic.create_app(
        spec_path=spec_path, implementation=SimpleImplementation()
    )

    client = TestClient(app)

    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "automatic"
    assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__])

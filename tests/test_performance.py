"""Performance tests for the automatic framework."""

import pytest
import time
import tempfile
import yaml
import asyncio
from pathlib import Path
import httpx
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import automatic


class FastTestImplementation:
    """Fast test implementation for performance testing."""
    
    def get_item(self, data):
        return {"id": data.get("item_id", 1), "name": "test_item"}, 200
    
    def create_item(self, data):
        return {"id": 123, "name": data.get("name", "new_item")}, 201
    
    def list_items(self, data):
        return {"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}, 200


@pytest.fixture
def fast_openapi_spec():
    """Create a simple OpenAPI specification optimized for speed."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Fast API", "version": "1.0.0"},
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
                    "responses": {
                        "200": {
                            "description": "Item retrieved",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
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
                                    "properties": {
                                        "name": {"type": "string"}
                                    },
                                    "required": ["name"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Item created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "get": {
                    "operationId": "list_items",
                    "responses": {
                        "200": {
                            "description": "List of items",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "items": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"}
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
            }
        }
    }
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(spec, f)
        return Path(f.name)


def test_response_time_under_200ms(fast_openapi_spec, tmp_path):
    """Test that framework components operate under 200ms."""
    # Create directory structure
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()
    
    # Copy spec and create implementation
    import shutil
    shutil.copy(fast_openapi_spec, api_dir / "fast.yaml")
    
    impl_code = '''
class Implementation:
    def get_item(self, data):
        return {"id": data.get("item_id", 1), "name": "test_item"}, 200
    
    def create_item(self, data):
        return {"id": 123, "name": data.get("name", "new_item")}, 201
    
    def list_items(self, data):
        return {"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}, 200
'''
    (impl_dir / "fast.py").write_text(impl_code)
    
    # Test app creation time
    start_time = time.perf_counter()
    app = automatic.create_app(api_dir=api_dir, impl_dir=impl_dir)
    end_time = time.perf_counter()
    
    creation_time_ms = (end_time - start_time) * 1000
    assert creation_time_ms < 200, f"App creation time {creation_time_ms:.2f}ms exceeds 200ms"
    
    # Test direct method calls (simulating what happens during requests)
    implementation = FastTestImplementation()
    start_time = time.perf_counter()
    result = implementation.get_item({"item_id": 123})
    end_time = time.perf_counter()
    
    method_time_ms = (end_time - start_time) * 1000
    assert method_time_ms < 200, f"Method call time {method_time_ms:.2f}ms exceeds 200ms"
    assert result[0]["id"] == 123
    assert result[1] == 200


def test_average_response_time_multiple_requests(fast_openapi_spec, tmp_path):
    """Test average method call time over multiple requests."""
    # Create directory structure
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()
    
    # Copy spec and create implementation
    import shutil
    shutil.copy(fast_openapi_spec, api_dir / "fast.yaml")
    
    impl_code = '''
class Implementation:
    def get_item(self, data):
        return {"id": data.get("item_id", 1), "name": "test_item"}, 200
    
    def create_item(self, data):
        return {"id": 123, "name": data.get("name", "new_item")}, 201
    
    def list_items(self, data):
        return {"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}, 200
'''
    (impl_dir / "fast.py").write_text(impl_code)
    
    implementation = FastTestImplementation()
    app = automatic.create_app(api_dir=api_dir, impl_dir=impl_dir)
    
    # Warm up (first call is often slower due to initialization)
    implementation.get_item({"item_id": 1})
    
    # Test multiple method calls
    num_requests = 10
    total_time = 0
    
    for i in range(num_requests):
        start_time = time.perf_counter()
        result = implementation.get_item({"item_id": i+1})
        end_time = time.perf_counter()
        
        assert result[1] == 200
        total_time += (end_time - start_time)
    
    average_time_ms = (total_time / num_requests) * 1000
    
    assert average_time_ms < 200, f"Average method call time {average_time_ms:.2f}ms exceeds 200ms"
    
    print(f"Average method call time over {num_requests} calls: {average_time_ms:.2f}ms")


def test_app_creation_time(fast_openapi_spec, tmp_path):
    """Test that app creation is fast."""
    # Create directory structure
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()
    
    # Copy spec and create implementation
    import shutil
    shutil.copy(fast_openapi_spec, api_dir / "fast.yaml")
    
    impl_code = '''
class Implementation:
    def get_item(self, data):
        return {"id": data.get("item_id", 1), "name": "test_item"}, 200
    
    def create_item(self, data):
        return {"id": 123, "name": data.get("name", "new_item")}, 201
    
    def list_items(self, data):
        return {"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}, 200
'''
    (impl_dir / "fast.py").write_text(impl_code)
    
    start_time = time.perf_counter()
    app = automatic.create_app(api_dir=api_dir, impl_dir=impl_dir)
    end_time = time.perf_counter()
    
    creation_time_ms = (end_time - start_time) * 1000
    
    # App creation should be reasonably fast (under 1 second)
    assert creation_time_ms < 1000, f"App creation time {creation_time_ms:.2f}ms exceeds 1000ms"
    
    print(f"App creation time: {creation_time_ms:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
"""Performance tests for the LiveAPI CRUD+ framework."""

import pytest
import time
import tempfile
import yaml
from pathlib import Path
import sys
import liveapi.implementation as liveapi

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def fast_openapi_spec():
    """Create a simple OpenAPI specification optimized for speed."""
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Fast API", "version": "1.0.0"},
        "components": {
            "schemas": {
                "Item": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                    "required": ["name"],
                },
                "ItemList": {
                    "type": "object",
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Item"},
                        }
                    },
                },
            }
        },
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
                    "responses": {
                        "200": {
                            "description": "Item retrieved",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            },
                        }
                    },
                }
            },
            "/items": {
                "post": {
                    "operationId": "create_item",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Item"}
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "Item created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            },
                        }
                    },
                },
                "get": {
                    "operationId": "list_items",
                    "responses": {
                        "200": {
                            "description": "List of items",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ItemList"}
                                }
                            },
                        }
                    },
                },
            },
        },
    }

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(spec, f)
        return Path(f.name)


def test_app_creation_under_500ms(fast_openapi_spec):
    """Test that app creation operates under 500ms."""
    start_time = time.perf_counter()
    app = liveapi.create_app(fast_openapi_spec)
    end_time = time.perf_counter()

    creation_time_ms = (end_time - start_time) * 1000
    assert (
        creation_time_ms < 500
    ), f"App creation time {creation_time_ms:.2f}ms exceeds 500ms"

    print(f"✅ App creation time: {creation_time_ms:.2f}ms")
    assert app is not None


def test_repeated_app_creation_performance(fast_openapi_spec):
    """Test average app creation time over multiple attempts."""
    # Warm up (first call is often slower due to initialization)
    liveapi.create_app(fast_openapi_spec)

    # Test multiple app creations
    num_requests = 5
    total_time = 0

    for i in range(num_requests):
        start_time = time.perf_counter()
        app = liveapi.create_app(fast_openapi_spec)
        end_time = time.perf_counter()

        assert app is not None
        total_time += end_time - start_time

    average_time_ms = (total_time / num_requests) * 1000

    assert (
        average_time_ms < 200
    ), f"Average app creation time {average_time_ms:.2f}ms exceeds 200ms"

    print(
        f"✅ Average app creation time over {num_requests} attempts: {average_time_ms:.2f}ms"
    )


@pytest.mark.asyncio
async def test_crud_handlers_performance():
    """Test that CRUD handlers are fast."""
    from pydantic import BaseModel

    class TestItem(BaseModel):
        id: int | None = None
        name: str

    handlers = liveapi.CRUDHandlers(TestItem, "items")

    # Test create performance
    times = []
    for i in range(20):
        start_time = time.perf_counter()
        result = await handlers.create({"name": f"item_{i}"})
        end_time = time.perf_counter()

        times.append((end_time - start_time) * 1000)
        assert result["name"] == f"item_{i}"

    avg_time = sum(times) / len(times)
    max_time = max(times)

    print(f"✅ CRUD create - Avg: {avg_time:.4f}ms, Max: {max_time:.4f}ms")

    assert avg_time < 5, f"Average CRUD create time {avg_time:.4f}ms exceeds 5ms"
    assert max_time < 20, f"Maximum CRUD create time {max_time:.4f}ms exceeds 20ms"


def test_pydantic_model_generation_performance(fast_openapi_spec):
    """Test that Pydantic model generation is fast."""
    parser = liveapi.LiveAPIParser(fast_openapi_spec)
    parser.load_spec()

    # Test model generation performance
    times = []
    for i in range(10):
        start_time = time.perf_counter()
        generator = liveapi.PydanticGenerator()
        generator.set_schema_definitions(parser.spec.get("components", {}))
        # Generate a model from the Item schema
        model = generator.generate_model_from_schema(
            parser.spec["components"]["schemas"]["Item"], "Item"
        )
        end_time = time.perf_counter()

        times.append((end_time - start_time) * 1000)
        assert model is not None

    avg_time = sum(times) / len(times)
    max_time = max(times)

    print(f"✅ Model generation - Avg: {avg_time:.2f}ms, Max: {max_time:.2f}ms")

    assert avg_time < 50, f"Average model generation time {avg_time:.2f}ms exceeds 50ms"
    assert (
        max_time < 100
    ), f"Maximum model generation time {max_time:.2f}ms exceeds 100ms"


def test_framework_startup_time(fast_openapi_spec):
    """Test overall framework startup performance."""
    print("\n=== Framework Startup Performance ===")

    # Measure complete app creation
    start_time = time.perf_counter()
    app = liveapi.create_app(fast_openapi_spec)
    end_time = time.perf_counter()

    startup_time_ms = (end_time - start_time) * 1000

    print(f"📊 Complete framework startup: {startup_time_ms:.2f}ms")

    # Framework should start reasonably fast
    assert (
        startup_time_ms < 1000
    ), f"Framework startup time {startup_time_ms:.2f}ms exceeds 1000ms"

    assert app is not None
    print("🎯 Framework demonstrates fast startup capability!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

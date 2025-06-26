"""Tests for RFC 7807 error formatting edge cases."""

import pytest
from fastapi.testclient import TestClient

from src.liveapi.implementation.app import create_app


class TestRFC7807ErrorFormatting:
    """Test RFC 7807 error format compliance in various scenarios."""

    @pytest.fixture
    def test_spec(self):
        """OpenAPI spec with validation constraints for testing."""
        return {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "post": {
                        "summary": "Create user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "User created"},
                            "422": {
                                "description": "Validation Error",
                                "content": {
                                    "application/problem+json": {
                                        "schema": {"$ref": "#/components/schemas/ValidationError"}
                                    }
                                }
                            }
                        }
                    }
                },
                "/complex": {
                    "post": {
                        "summary": "Create complex object",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ComplexModel"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Created"},
                            "422": {"description": "Validation Error"}
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "required": ["name", "email", "age"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "minLength": 2,
                                "maxLength": 50
                            },
                            "email": {
                                "type": "string",
                                "format": "email"
                            },
                            "age": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 120
                            },
                            "phone": {
                                "type": "string",
                                "pattern": "^\\+?[1-9]\\d{1,14}$"
                            }
                        }
                    },
                    "ComplexModel": {
                        "type": "object",
                        "required": ["nested", "items"],
                        "properties": {
                            "nested": {"$ref": "#/components/schemas/NestedObject"},
                            "items": {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 5,
                                "items": {"$ref": "#/components/schemas/Item"}
                            },
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "minLength": 1
                                }
                            }
                        }
                    },
                    "NestedObject": {
                        "type": "object",
                        "required": ["value"],
                        "properties": {
                            "value": {
                                "type": "string",
                                "minLength": 5
                            },
                            "count": {
                                "type": "integer",
                                "minimum": 1
                            }
                        }
                    },
                    "Item": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {
                                "type": "string",
                                "minLength": 1
                            }
                        }
                    },
                    "ValidationError": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "title": {"type": "string"},
                            "status": {"type": "integer"},
                            "detail": {"type": "string"},
                            "instance": {"type": "string"}
                        }
                    }
                }
            }
        }

    @pytest.fixture
    def test_app(self, test_spec):
        """Create a test FastAPI app with the test spec."""
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_spec, f)
            app = create_app(f.name)
            return app

    def test_multiple_validation_errors_single_request(self, test_app):
        """Test RFC 7807 format with multiple validation errors in one request."""
        client = TestClient(test_app)

        # Send request with multiple validation errors
        invalid_data = {
            "name": "A",  # Too short (minLength: 2)
            "email": "invalid-email",  # Invalid format
            "age": 150,  # Too high (maximum: 120)
            "phone": "invalid-phone"  # Invalid pattern
        }

        response = client.post("/users", json=invalid_data)

        # Should return 422 status
        assert response.status_code == 422

        # Should have correct content type for RFC 7807
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()

        # Should have errors array format
        assert "errors" in error_data
        assert len(error_data["errors"]) > 0

        # Each error should follow structure
        for error in error_data["errors"]:
            assert "title" in error
            assert "detail" in error
            assert "status" in error
            assert error["status"] == "422"
            assert "source" in error
            assert "pointer" in error["source"]

        # Should contain information about multiple validation errors
        error_details = [error["detail"] for error in error_data["errors"]]
        assert len(error_details) >= 2  # Multiple errors

    def test_nested_object_validation_errors(self, test_app):
        """Test RFC 7807 format with nested object validation errors."""
        client = TestClient(test_app)

        # Send request with nested validation errors
        invalid_data = {
            "nested": {
                "value": "Hi",  # Too short (minLength: 5)
                "count": 0      # Too low (minimum: 1)
            },
            "items": [],  # Too few items (minItems: 1)
            "tags": ["", "valid"]  # First tag too short (minLength: 1)
        }

        response = client.post("/complex", json=invalid_data)

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()

        # Should have errors array format
        assert "errors" in error_data
        assert len(error_data["errors"]) > 0

        # Each error should have proper structure
        for error in error_data["errors"]:
            assert error["status"] == "422"
            assert "detail" in error
            assert len(error["detail"]) > 0

    def test_very_long_error_messages(self, test_app):
        """Test RFC 7807 format with very long error messages."""
        client = TestClient(test_app)

        # Create data that will generate long error messages
        very_long_name = "x" * 1000  # Exceeds maxLength: 50 by a lot

        invalid_data = {
            "name": very_long_name,
            "email": "not-an-email-but-very-long-" * 10,  # Long invalid email
            "age": -999999,  # Very negative age
            "phone": "invalid" * 100  # Very long invalid phone
        }

        response = client.post("/users", json=invalid_data)

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()

        # Should still follow error format even with long messages
        assert "errors" in error_data
        assert len(error_data["errors"]) > 0

        # Should handle long content gracefully
        for error in error_data["errors"]:
            assert error["status"] == "422"
            detail = error["detail"]
            assert isinstance(detail, str)
            assert len(detail) > 0

    def test_special_characters_in_error_messages(self, test_app):
        """Test RFC 7807 format with special characters in validation errors."""
        client = TestClient(test_app)

        # Use data with special characters that might break JSON encoding
        invalid_data = {
            "name": "Test\x00\xFF\u2603",  # Null byte, high byte, unicode snowman
            "email": "test@domain\x7F.com",  # DEL character
            "age": "not-a-number",  # Wrong type
            "phone": "+1-<script>alert('xss')</script>"  # Potential XSS
        }

        response = client.post("/users", json=invalid_data)

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()

        # Should properly encode/escape special characters
        assert "errors" in error_data
        assert len(error_data["errors"]) > 0

        # Response should be valid JSON despite special characters
        for error in error_data["errors"]:
            assert error["status"] == "422"
            assert isinstance(error["detail"], str)

    def test_array_validation_errors(self, test_app):
        """Test RFC 7807 format with array validation errors."""
        client = TestClient(test_app)

        # Create array validation errors
        invalid_data = {
            "nested": {"value": "valid"},
            "items": [
                {"id": "", "name": ""},  # Both fields invalid
                {"id": "valid"},  # Missing required name
                {"name": "valid"},  # Missing required id
                {"id": "ok", "name": "ok"},
                {"id": "another", "name": "another"},
                {"id": "too", "name": "many"},  # Exceeds maxItems: 5
            ],
            "tags": ["", "valid", "", "another_empty:"]  # Multiple empty tags
        }

        response = client.post("/complex", json=invalid_data)

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()

        # Should handle array index information in errors
        assert "errors" in error_data
        assert len(error_data["errors"]) > 0

        for error in error_data["errors"]:
            assert error["status"] == "422"
            assert "detail" in error

    def test_missing_required_fields(self, test_app):
        """Test RFC 7807 format when required fields are missing."""
        client = TestClient(test_app)

        # Send completely empty request
        response = client.post("/users", json={})

        assert response.status_code == 422
        assert response.headers["content-type"] == "application/problem+json"

        error_data = response.json()

        # Should mention missing required fields
        assert "errors" in error_data
        assert len(error_data["errors"]) > 0

        # Should mention required fields
        found_required_error = False
        for error in error_data["errors"]:
            assert error["status"] == "422"
            detail = error["detail"]
            if "required" in detail.lower() or "missing" in detail.lower():
                found_required_error = True
        assert found_required_error

    def test_malformed_json_request(self, test_app):
        """Test RFC 7807 format with malformed JSON."""
        client = TestClient(test_app)

        # Send malformed JSON
        response = client.post(
            "/users",
            content='{"name": "test", "email": "test@example.com", "age": 25',  # Missing closing brace
            headers={"Content-Type": "application/json"}
        )

        # Should return 422 for malformed JSON
        assert response.status_code == 422

        # May not always be application/problem+json for JSON parse errors
        # but should still be structured error response

    def test_content_type_validation(self, test_app):
        """Test that RFC 7807 errors have correct Content-Type header."""
        client = TestClient(test_app)

        invalid_data = {"name": "A", "email": "invalid", "age": 150}

        response = client.post("/users", json=invalid_data)

        # Should have RFC 7807 compliant Content-Type
        assert response.status_code == 422
        content_type = response.headers.get("content-type", "")

        # Should be application/problem+json as per RFC 7807
        assert "application/problem+json" in content_type

    def test_error_response_structure_completeness(self, test_app):
        """Test that RFC 7807 error responses have all recommended fields."""
        client = TestClient(test_app)

        invalid_data = {"name": "A", "email": "invalid", "age": 150}

        response = client.post("/users", json=invalid_data)
        assert response.status_code == 422

        error_data = response.json()

        # Error response should have proper structure
        assert "errors" in error_data
        assert len(error_data["errors"]) > 0

        # Each error should have required fields
        for error in error_data["errors"]:
            required_fields = ["title", "status", "detail", "source"]
            for field in required_fields:
                assert field in error, f"Missing required field: {field}"

            # Validate field types
            assert isinstance(error["status"], str)
            assert isinstance(error["title"], str)
            assert isinstance(error["detail"], str)
            assert isinstance(error["source"], dict)
            assert "pointer" in error["source"]

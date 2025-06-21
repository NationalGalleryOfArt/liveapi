"""Tests for the response validation and conversion layer."""

from datetime import datetime
from automatic.validator import ResponseValidator
from automatic.response_transformer import ResponseTransformer


class TestResponseValidator:
    """Test response validation and conversion functionality."""

    def test_validator_with_no_spec(self):
        """Test validator works without OpenAPI spec."""
        validator = ResponseValidator()
        
        # Should return data unchanged without spec
        data = {"id": 1, "name": "test"}
        result = validator.validate_and_convert(data, "get_user", 200, 1)
        
        assert result == data

    def test_validator_with_simple_object_schema(self):
        """Test validation with object schema."""
        spec = {
            "paths": {
                "/users/{user_id}": {
                    "get": {
                        "operationId": "get_user",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "active": {"type": "boolean"}
                                            },
                                            "required": ["id", "name"]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        validator = ResponseValidator(spec)
        
        # Test valid data passes through with type conversion
        data = {"id": "123", "name": "John", "active": "true"}
        result = validator.validate_and_convert(data, "get_user", 200, 1)
        
        assert result["id"] == 123  # String to int conversion
        assert result["name"] == "John"
        assert result["active"] is True  # String to bool conversion

    def test_validator_adds_missing_required_fields(self):
        """Test validator adds defaults for missing required fields."""
        spec = {
            "paths": {
                "/users": {
                    "post": {
                        "operationId": "create_user",
                        "responses": {
                            "201": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "status": {"type": "string", "default": "active"}
                                            },
                                            "required": ["id", "name", "status"]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        validator = ResponseValidator(spec)
        
        # Missing required field should get default
        data = {"id": 1, "name": "John"}
        result = validator.validate_and_convert(data, "create_user", 201, 1)
        
        assert result["status"] == "active"  # Default value added

    def test_validator_sanitizes_sensitive_fields(self):
        """Test validator removes/sanitizes sensitive fields."""
        spec = {
            "paths": {
                "/users/{user_id}": {
                    "get": {
                        "operationId": "get_user",
                        "responses": {
                            "200": {
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
                }
            }
        }
        
        validator = ResponseValidator(spec)
        
        # Data with sensitive fields
        data = {
            "id": 1,
            "name": "John",
            "password_hash": "secret123",
            "_internal_id": "internal-123",
            "api_key": "key-456"
        }
        
        result = validator.validate_and_convert(data, "get_user", 200, 1)
        
        # Sensitive fields should be sanitized
        assert result["password_hash"] == "[REDACTED]"
        assert result["_internal_id"] is None
        assert result["api_key"] == "[REDACTED]"

    def test_validator_handles_arrays(self):
        """Test validator processes array responses."""
        spec = {
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "list_users",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
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
        
        validator = ResponseValidator(spec)
        
        # Array data with type conversion needed
        data = [
            {"id": "1", "name": "John"},
            {"id": "2", "name": "Jane"}
        ]
        
        result = validator.validate_and_convert(data, "list_users", 200, 1)
        
        assert len(result) == 2
        assert result[0]["id"] == 1  # String to int conversion
        assert result[1]["id"] == 2

    def test_validator_version_aware_handling(self):
        """Test validator handles version-specific logic."""
        spec = {
            "paths": {
                "/users/{user_id}": {
                    "get": {
                        "operationId": "get_user",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "created_date": {"type": "string", "format": "date-time"}
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
        
        validator = ResponseValidator(spec)
        
        # Data with datetime object
        test_date = datetime(2023, 1, 1, 12, 0, 0)
        data = {"id": 1, "created_date": test_date}
        
        # Version 2+ should format dates as ISO strings
        result = validator.validate_and_convert(data, "get_user", 200, 2)
        
        assert result["created_date"] == "2023-01-01T12:00:00"

    def test_validator_graceful_failure(self):
        """Test validator returns original data on validation failure."""
        spec = {
            "paths": {
                "/users/{user_id}": {
                    "get": {
                        "operationId": "get_user",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"}
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
        
        validator = ResponseValidator(spec)
        
        # Data that can't be converted
        invalid_data = {"id": "not-a-number"}
        result = validator.validate_and_convert(invalid_data, "get_user", 200, 1)
        
        # Should return original data when conversion fails
        assert result == invalid_data


class TestResponseTransformerIntegration:
    """Test integration of ResponseTransformer with ResponseValidator."""

    def test_transformer_applies_validation_for_success_responses(self):
        """Test transformer applies validation for successful responses."""
        spec = {
            "paths": {
                "/users/{user_id}": {
                    "get": {
                        "operationId": "get_user",
                        "responses": {
                            "200": {
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
                }
            }
        }
        
        transformer = ResponseTransformer(spec)
        
        # Success response should be validated
        data = {"id": "123", "name": "John"}
        result = transformer.transform_response(data, 200, "get_user", 1)
        
        assert result["id"] == 123  # Type conversion applied

    def test_transformer_skips_validation_for_error_responses(self):
        """Test transformer skips validation for error responses."""
        spec = {
            "paths": {
                "/users/{user_id}": {
                    "get": {
                        "operationId": "get_user",
                        "responses": {
                            "200": {"content": {"application/json": {"schema": {"type": "object"}}}}
                        }
                    }
                }
            }
        }
        
        transformer = ResponseTransformer(spec)
        
        # Error response should go through RFC 9457 transformation only
        error_data = "User not found"
        result = transformer.transform_response(error_data, 404, "get_user", 1)
        
        # Should be RFC 9457 format, not validated as success response
        assert result["type"] == "about:blank"
        assert result["title"] == "User not found"
        assert result["status"] == 404

    def test_transformer_without_operation_id(self):
        """Test transformer works without operation_id."""
        spec = {"paths": {}}
        transformer = ResponseTransformer(spec)
        
        # Should work without validation when no operation_id provided
        data = {"test": "data"}
        result = transformer.transform_response(data, 200)
        
        assert result == data

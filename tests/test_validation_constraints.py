"""Test validation constraints from OpenAPI schemas."""

import pytest
import tempfile
import yaml
from pathlib import Path
from fastapi.testclient import TestClient

from src.liveapi.implementation.app import create_app
from src.liveapi.implementation.pydantic_generator import PydanticGenerator


class TestJSONSchemaValidationConstraints:
    """Test that JSON Schema validation constraints are properly enforced."""
    
    @pytest.fixture
    def test_spec(self):
        """OpenAPI spec with various validation constraints."""
        return {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/products": {
                    "post": {
                        "operationId": "create_product",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Product"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Created"}
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "Product": {
                        "type": "object",
                        "required": ["name", "price", "category"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {
                                "type": "string",
                                "minLength": 2,
                                "maxLength": 100,
                                "pattern": "^[A-Za-z0-9 ]+$"
                            },
                            "description": {
                                "type": "string",
                                "maxLength": 500
                            },
                            "price": {
                                "type": "number",
                                "minimum": 0.01,
                                "maximum": 99999.99
                            },
                            "quantity": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 10000
                            },
                            "category": {
                                "type": "string",
                                "enum": ["electronics", "clothing", "books", "food"]
                            },
                            "tags": {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 10,
                                "items": {"type": "string"}
                            },
                            "active": {"type": "boolean"}
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def test_client(self, test_spec):
        """Create FastAPI test client from spec."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_spec, f)
            spec_path = f.name
        
        try:
            app = create_app(spec_path)
            return TestClient(app)
        finally:
            Path(spec_path).unlink()
    
    def test_pydantic_model_generation_with_constraints(self, test_spec):
        """Test that Pydantic models are generated with proper validation constraints."""
        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(test_spec["components"])
        
        ProductModel = generator.generate_model_from_schema(
            test_spec["components"]["schemas"]["Product"], 
            "Product"
        )
        
        # Test valid data
        valid_product = ProductModel(
            name="Test Product",
            price=19.99,
            category="electronics",
            description="A great product",
            quantity=5,
            tags=["tech", "gadget"],
            active=True
        )
        assert valid_product.name == "Test Product"
        assert valid_product.price == 19.99
        
        # Test minLength constraint
        with pytest.raises(Exception) as exc_info:
            ProductModel(name="A", price=19.99, category="electronics")
        assert "at least 2 characters" in str(exc_info.value).lower()
        
        # Test maxLength constraint  
        with pytest.raises(Exception) as exc_info:
            ProductModel(
                name="A" * 101,  # Too long
                price=19.99, 
                category="electronics"
            )
        assert "at most 100 characters" in str(exc_info.value).lower()
        
        # Test pattern constraint
        with pytest.raises(Exception) as exc_info:
            ProductModel(
                name="Test@Product!",  # Invalid characters
                price=19.99, 
                category="electronics"
            )
        assert "string should match pattern" in str(exc_info.value).lower()
        
        # Test minimum constraint
        with pytest.raises(Exception) as exc_info:
            ProductModel(name="Test", price=0.0, category="electronics")
        assert "greater than or equal to 0.01" in str(exc_info.value).lower()
        
        # Test maximum constraint
        with pytest.raises(Exception) as exc_info:
            ProductModel(name="Test", price=100000.0, category="electronics")
        assert "less than or equal to 99999.99" in str(exc_info.value).lower()
        
        # Test enum constraint
        with pytest.raises(Exception) as exc_info:
            ProductModel(name="Test", price=19.99, category="invalid_category")
        error_msg = str(exc_info.value).lower()
        assert ("not a valid enumeration member" in error_msg or 
                "input should be" in error_msg or
                "literal_error" in error_msg or
                "unexpected value" in error_msg)
        
        # Test minItems constraint
        with pytest.raises(Exception) as exc_info:
            ProductModel(
                name="Test", 
                price=19.99, 
                category="electronics",
                tags=[]  # Empty array
            )
        assert "at least 1 item" in str(exc_info.value).lower()
        
        # Test maxItems constraint
        with pytest.raises(Exception) as exc_info:
            ProductModel(
                name="Test", 
                price=19.99, 
                category="electronics",
                tags=["tag"] * 11  # Too many items
            )
        assert "at most 10 items" in str(exc_info.value).lower()


class TestHTTP422ErrorResponses:
    """Test HTTP 422 error responses from FastAPI endpoints."""
    
    @pytest.fixture
    def test_spec(self):
        """Simple OpenAPI spec with validation constraints."""
        return {
            "openapi": "3.0.3",
            "info": {"title": "User API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "post": {
                        "operationId": "create_user",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        },
                        "responses": {
                            "201": {"description": "Created"}
                        }
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "required": ["username", "email"],
                        "properties": {
                            "id": {"type": "string"},
                            "username": {
                                "type": "string",
                                "minLength": 3,
                                "maxLength": 20,
                                "pattern": "^[a-zA-Z0-9_]+$"
                            },
                            "email": {
                                "type": "string",
                                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                            },
                            "age": {
                                "type": "integer",
                                "minimum": 13,
                                "maximum": 120
                            }
                        }
                    }
                }
            }
        }
    
    @pytest.fixture
    def test_client(self, test_spec):
        """Create FastAPI test client from spec."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_spec, f)
            spec_path = f.name
        
        try:
            app = create_app(spec_path)
            return TestClient(app)
        finally:
            Path(spec_path).unlink()
    
    def test_valid_request_succeeds(self, test_client):
        """Test that valid requests return 201."""
        valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "age": 25
        }
        
        response = test_client.post("/users", json=valid_data)
        assert response.status_code == 201
        
        # Verify the response contains the data
        result = response.json()
        assert result["username"] == "testuser"
        assert result["email"] == "test@example.com"
        assert result["age"] == 25
        assert "id" in result  # ID should be auto-generated
    
    def test_missing_required_field_returns_422(self, test_client):
        """Test that missing required fields return 422."""
        invalid_data = {
            "username": "testuser"
            # Missing required "email" field
        }
        
        response = test_client.post("/users", json=invalid_data)
        assert response.status_code == 422
        assert response.headers.get("content-type") == "application/problem+json"
        
        error_data = response.json()
        assert "errors" in error_data
        assert len(error_data["errors"]) == 1
        
        error = error_data["errors"][0]
        assert error["title"] == "Unprocessable Entity"
        assert "required" in error["detail"].lower()
        assert error["status"] == "422"
        assert "email" in error["source"]["pointer"]
    
    def test_minlength_validation_returns_422(self, test_client):
        """Test that minLength validation returns 422."""
        invalid_data = {
            "username": "ab",  # Too short (minLength: 3)
            "email": "test@example.com"
        }
        
        response = test_client.post("/users", json=invalid_data)
        assert response.status_code == 422
        assert response.headers.get("content-type") == "application/problem+json"
        
        error_data = response.json()
        assert "errors" in error_data
        
        error = error_data["errors"][0]
        assert error["title"] == "Unprocessable Entity"
        assert "at least 3 characters" in error["detail"].lower()
        assert error["status"] == "422"
        assert "username" in error["source"]["pointer"]
    
    def test_pattern_validation_returns_422(self, test_client):
        """Test that pattern validation returns 422."""
        invalid_data = {
            "username": "test-user!",  # Invalid characters (pattern: ^[a-zA-Z0-9_]+$)
            "email": "test@example.com"
        }
        
        response = test_client.post("/users", json=invalid_data)
        assert response.status_code == 422
        assert response.headers.get("content-type") == "application/problem+json"
        
        error_data = response.json()
        assert "errors" in error_data
        
        error = error_data["errors"][0]
        assert error["title"] == "Unprocessable Entity"
        assert "should match pattern" in error["detail"].lower()
        assert error["status"] == "422"
        assert "username" in error["source"]["pointer"]
    
    def test_invalid_email_pattern_returns_422(self, test_client):
        """Test that invalid email pattern returns 422."""
        invalid_data = {
            "username": "testuser",
            "email": "not-an-email"  # Invalid email format
        }
        
        response = test_client.post("/users", json=invalid_data)
        assert response.status_code == 422
        assert response.headers.get("content-type") == "application/problem+json"
        
        error_data = response.json()
        assert "errors" in error_data
        
        error = error_data["errors"][0]
        assert error["title"] == "Unprocessable Entity"
        assert "should match pattern" in error["detail"].lower()
        assert error["status"] == "422"
        assert "email" in error["source"]["pointer"]
    
    def test_numeric_constraints_return_422(self, test_client):
        """Test that numeric constraints return 422."""
        # Test minimum constraint
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "age": 12  # Too young (minimum: 13)
        }
        
        response = test_client.post("/users", json=invalid_data)
        assert response.status_code == 422
        assert response.headers.get("content-type") == "application/problem+json"
        
        error_data = response.json()
        assert "errors" in error_data
        
        error = error_data["errors"][0]
        assert error["title"] == "Unprocessable Entity"
        assert "greater than or equal to 13" in error["detail"].lower()
        assert error["status"] == "422"
        assert "age" in error["source"]["pointer"]
        
        # Test maximum constraint
        invalid_data["age"] = 121  # Too old (maximum: 120)
        
        response = test_client.post("/users", json=invalid_data)
        assert response.status_code == 422
        
        error_data = response.json()
        error = error_data["errors"][0]
        assert "less than or equal to 120" in error["detail"].lower()
    
    def test_multiple_validation_errors_return_422(self, test_client):
        """Test that multiple validation errors are all returned."""
        invalid_data = {
            "username": "ab",  # Too short
            "email": "not-an-email",  # Invalid format
            "age": 12  # Too young
        }
        
        response = test_client.post("/users", json=invalid_data)
        assert response.status_code == 422
        assert response.headers.get("content-type") == "application/problem+json"
        
        error_data = response.json()
        assert "errors" in error_data
        assert len(error_data["errors"]) == 3  # Should have all three errors
        
        # Check that all fields have errors
        error_fields = [error["source"]["pointer"] for error in error_data["errors"]]
        assert any("username" in field for field in error_fields)
        assert any("email" in field for field in error_fields)
        assert any("age" in field for field in error_fields)
    
    def test_openapi_spec_has_correct_422_schema(self, test_client):
        """Test that the OpenAPI spec shows the correct 422 error schema."""
        # Get the OpenAPI spec
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_spec = response.json()
        
        # Check ValidationError schema
        validation_error_schema = openapi_spec["components"]["schemas"]["ValidationError"]
        
        # Should have RFC 7807 format
        assert validation_error_schema["type"] == "object"
        assert "errors" in validation_error_schema["properties"]
        assert validation_error_schema["properties"]["errors"]["type"] == "array"
        
        # Check error item schema
        error_item = validation_error_schema["properties"]["errors"]["items"]
        assert "title" in error_item["properties"]
        assert "detail" in error_item["properties"] 
        assert "status" in error_item["properties"]
        assert "source" in error_item["properties"]
        
        # Check that POST /users has 422 response
        post_users = openapi_spec["paths"]["/users"]["post"]
        assert "422" in post_users["responses"]
        
        error_response = post_users["responses"]["422"]
        assert error_response["description"] == "Validation Error"
        assert "application/problem+json" in error_response["content"]
        
        schema_ref = error_response["content"]["application/problem+json"]["schema"]["$ref"]
        assert schema_ref == "#/components/schemas/ValidationError"
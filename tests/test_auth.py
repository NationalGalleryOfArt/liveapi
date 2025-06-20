"""Tests for authentication functionality."""

import pytest
from fastapi.testclient import TestClient
from automatic import create_app, create_api_key_auth, create_bearer_auth, ValidationError, NotFoundError


class TestImplementation:
    """Test implementation with authentication."""
    
    def __init__(self):
        self.users = {'1': {'id': '1', 'name': 'John', 'email': 'john@example.com'}}
    
    def list_users(self, data):
        """List users (requires auth)."""
        auth_info = data.get('auth')
        if not auth_info:
            from automatic import UnauthorizedError
            raise UnauthorizedError("Authentication required")
        return list(self.users.values()), 200
    
    def get_user(self, data):
        """Get user by ID (requires auth)."""
        auth_info = data.get('auth')
        if not auth_info:
            from automatic import UnauthorizedError
            raise UnauthorizedError("Authentication required")
        
        user_id = data.get('user_id')
        if user_id not in self.users:
            raise NotFoundError(f"User {user_id} not found")
        return self.users[user_id], 200
    
    def health_check(self, data):
        """Public health check (no auth required)."""
        return {"status": "healthy"}, 200


@pytest.fixture
def test_spec_content():
    return """
openapi: 3.0.3
info:
  title: Test API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: list_users
      summary: List users
      responses:
        '200':
          description: Success
  /users/{user_id}:
    get:
      operationId: get_user
      summary: Get user
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
        '404':
          description: Not found
  /health:
    get:
      operationId: health_check
      summary: Health check
      responses:
        '200':
          description: Success
"""


@pytest.fixture
def app_with_auth(test_spec_content, tmp_path):
    """Create test app with authentication."""
    # Write spec to temp file
    spec_file = tmp_path / "test_api.yaml"
    spec_file.write_text(test_spec_content)
    
    # Create auth
    auth = create_api_key_auth(api_keys=['test-key-123', 'test-key-456'])
    
    # Create app
    app = create_app(
        spec_path=str(spec_file),
        implementation=TestImplementation(),
        auth_dependency=auth
    )
    
    return app


@pytest.fixture
def app_no_auth(test_spec_content, tmp_path):
    """Create test app without authentication."""
    # Write spec to temp file
    spec_file = tmp_path / "test_api.yaml"
    spec_file.write_text(test_spec_content)
    
    # Create app
    app = create_app(
        spec_path=str(spec_file),
        implementation=TestImplementation()
    )
    
    return app


def test_authenticated_request_with_valid_header(app_with_auth):
    """Test authenticated request with valid API key in header."""
    client = TestClient(app_with_auth)
    
    response = client.get("/users", headers={"X-API-Key": "test-key-123"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "John"


def test_authenticated_request_with_second_valid_header(app_with_auth):
    """Test authenticated request with second valid API key in header."""
    client = TestClient(app_with_auth)
    
    response = client.get("/users", headers={"X-API-Key": "test-key-456"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "John"


def test_authenticated_request_without_key(app_with_auth):
    """Test authenticated request without API key."""
    client = TestClient(app_with_auth)
    
    response = client.get("/users")
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["title"] == "Unauthorized"
    assert "API key required" in data["detail"]["detail"]


def test_authenticated_request_with_invalid_key(app_with_auth):
    """Test authenticated request with invalid API key."""
    client = TestClient(app_with_auth)
    
    response = client.get("/users", headers={"X-API-Key": "invalid-key"})
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["title"] == "Unauthorized"
    assert "Invalid API key" in data["detail"]["detail"]


def test_authenticated_request_with_path_params(app_with_auth):
    """Test authenticated request with path parameters."""
    client = TestClient(app_with_auth)
    
    # Valid user
    response = client.get("/users/1", headers={"X-API-Key": "test-key-123"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["name"] == "John"
    
    # Invalid user
    response = client.get("/users/999", headers={"X-API-Key": "test-key-123"})
    assert response.status_code == 404
    data = response.json()
    assert data["title"] == "NotFound"
    assert "User 999 not found" in data["detail"]


def test_public_endpoint_with_auth_configured(app_with_auth):
    """Test that public endpoints work when auth is provided."""
    client = TestClient(app_with_auth)
    
    # When global auth is configured, all endpoints require auth
    # Public endpoint should work with auth
    response = client.get("/health", headers={"X-API-Key": "test-key-123"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    # Public endpoint should fail without auth when global auth is configured
    response = client.get("/health")
    assert response.status_code == 401


def test_no_auth_configured(app_no_auth):
    """Test that app works normally when no auth is configured."""
    client = TestClient(app_no_auth)
    
    # Should fail because implementation requires auth but no auth is configured
    response = client.get("/users")
    assert response.status_code == 401
    data = response.json()
    assert data["title"] == "Unauthorized"
    
    # Should also fail with auth header (no auth validation configured)
    response = client.get("/users", headers={"X-API-Key": "any-key"})
    assert response.status_code == 401
    
    # But public endpoint should work
    response = client.get("/health")
    assert response.status_code == 200


def test_auth_info_passed_to_implementation(app_with_auth):
    """Test that auth info is properly passed to implementation methods."""
    client = TestClient(app_with_auth)
    
    # This is implicitly tested by the other tests - if auth info wasn't passed,
    # the implementation would raise an exception about missing auth
    response = client.get("/users", headers={"X-API-Key": "test-key-123"})
    assert response.status_code == 200


def test_create_api_key_auth_variations():
    """Test different ways to create API key auth."""
    # Single string
    auth1 = create_api_key_auth(api_keys="single-key")
    assert hasattr(auth1, 'api_keys')
    assert "single-key" in auth1.api_keys
    
    # List of strings
    auth2 = create_api_key_auth(api_keys=["key1", "key2"])
    assert "key1" in auth2.api_keys
    assert "key2" in auth2.api_keys
    
    # Dict with metadata
    auth3 = create_api_key_auth(api_keys={"admin": {"role": "admin"}})
    assert "admin" in auth3.api_keys
    assert auth3.api_keys["admin"]["role"] == "admin"


# Bearer Token Authentication Tests

@pytest.fixture
def app_with_bearer_auth(test_spec_content, tmp_path):
    """Create test app with Bearer token authentication."""
    # Write spec to temp file
    spec_file = tmp_path / "test_api.yaml"
    spec_file.write_text(test_spec_content)
    
    # Create Bearer auth
    auth = create_bearer_auth(tokens=['bearer-token-123', 'bearer-token-456'])
    
    # Create app
    app = create_app(
        spec_path=str(spec_file),
        implementation=TestImplementation(),
        auth_dependency=auth
    )
    
    return app


def test_bearer_request_with_valid_token(app_with_bearer_auth):
    """Test authenticated request with valid Bearer token."""
    client = TestClient(app_with_bearer_auth)
    
    response = client.get("/users", headers={"Authorization": "Bearer bearer-token-123"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "John"


def test_bearer_request_with_second_valid_token(app_with_bearer_auth):
    """Test authenticated request with second valid Bearer token."""
    client = TestClient(app_with_bearer_auth)
    
    response = client.get("/users", headers={"Authorization": "Bearer bearer-token-456"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "John"


def test_bearer_request_without_token(app_with_bearer_auth):
    """Test authenticated request without Bearer token."""
    client = TestClient(app_with_bearer_auth)
    
    response = client.get("/users")
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["title"] == "Unauthorized"
    assert "Bearer token required" in data["detail"]["detail"]


def test_bearer_request_with_invalid_token(app_with_bearer_auth):
    """Test authenticated request with invalid Bearer token."""
    client = TestClient(app_with_bearer_auth)
    
    response = client.get("/users", headers={"Authorization": "Bearer invalid-token"})
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["title"] == "Unauthorized"
    assert "Invalid bearer token" in data["detail"]["detail"]


def test_bearer_request_with_malformed_header(app_with_bearer_auth):
    """Test authenticated request with malformed Authorization header."""
    client = TestClient(app_with_bearer_auth)
    
    # Missing Bearer prefix
    response = client.get("/users", headers={"Authorization": "invalid-token"})
    assert response.status_code == 401
    
    # Wrong case
    response = client.get("/users", headers={"Authorization": "bearer invalid-token"})
    assert response.status_code == 401


def test_create_bearer_auth_variations():
    """Test different ways to create Bearer auth."""
    # Single string
    auth1 = create_bearer_auth(tokens="single-token")
    assert hasattr(auth1, 'tokens')
    assert "single-token" in auth1.tokens
    
    # List of strings
    auth2 = create_bearer_auth(tokens=["token1", "token2"])
    assert "token1" in auth2.tokens
    assert "token2" in auth2.tokens
    
    # Dict with metadata
    auth3 = create_bearer_auth(tokens={"admin-token": {"role": "admin"}})
    assert "admin-token" in auth3.tokens
    assert auth3.tokens["admin-token"]["role"] == "admin"
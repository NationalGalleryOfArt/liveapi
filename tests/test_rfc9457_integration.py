"""Integration tests for RFC 9457 error response transformation."""

import importlib.util
from fastapi.testclient import TestClient
from src.automatic.app import create_app


class TestImplementation:
    """Test implementation for RFC 9457 testing."""

    def get_user(self, data):
        return {"user_id": 1, "name": "Test User"}, 200


def test_string_error_transforms_to_rfc9457(tmp_path):
    """Test that string errors are automatically transformed to RFC 9457 format."""
    # Create directory structure
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()

    # Create a simple users.yaml file
    users_spec = """
openapi: 3.0.3
info:
  title: Users API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: get_users
      responses:
        '200':
          description: List of users
    post:
      operationId: create_user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: User created
  /users/{user_id}:
    get:
      operationId: get_user
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
        '404':
          description: User not found
"""
    (api_dir / "users.yaml").write_text(users_spec)

    # Create test implementation
    impl_code = """
class Implementation:
    def get_users(self, data):
        return [], 200
    
    def get_user(self, data):
        return "User not found", 404
    
    def create_user(self, data):
        return {"user_id": 1, "name": data["name"]}, 201
"""
    (impl_dir / "users.py").write_text(impl_code)

    # Load implementation directly
    spec = importlib.util.spec_from_file_location(
        "implementation_module", impl_dir / "users.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    implementation = module.Implementation()

    test_app = create_app(
        spec_path=api_dir / "users.yaml", implementation=implementation
    )

    client = TestClient(test_app)
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json() == {
        "type": "about:blank",
        "title": "User not found",
        "status": 404,
    }


def test_dict_error_enhanced_to_rfc9457(tmp_path):
    """Test that dict errors are enhanced with RFC 9457 fields."""
    # Create directory structure
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()

    # Create a simple users.yaml file
    users_spec = """
openapi: 3.0.3
info:
  title: Users API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: get_users
      responses:
        '200':
          description: List of users
    post:
      operationId: create_user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: User created
  /users/{user_id}:
    get:
      operationId: get_user
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
        '404':
          description: User not found
"""
    (api_dir / "users.yaml").write_text(users_spec)

    # Create test implementation
    impl_code = """
class Implementation:
    def get_users(self, data):
        return [], 200
    
    def get_user(self, data):
        return {"message": "User validation failed", "field": "user_id"}, 400
    
    def create_user(self, data):
        return {"user_id": 1, "name": data["name"]}, 201
"""
    (impl_dir / "users.py").write_text(impl_code)

    # Load implementation directly
    spec = importlib.util.spec_from_file_location(
        "implementation_module", impl_dir / "users.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    implementation = module.Implementation()

    test_app = create_app(
        spec_path=api_dir / "users.yaml", implementation=implementation
    )

    client = TestClient(test_app)
    response = client.get("/users/999")

    assert response.status_code == 400
    json_response = response.json()

    # Should have RFC 9457 fields added
    assert json_response["type"] == "about:blank"
    assert json_response["title"] == "User validation failed"
    assert json_response["status"] == 400

    # Should preserve original fields
    assert json_response["message"] == "User validation failed"
    assert json_response["field"] == "user_id"


def test_rfc9457_compliant_error_passed_through(tmp_path):
    """Test that RFC 9457 compliant errors are passed through unchanged."""
    # Create directory structure
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()

    # Create a simple users.yaml file
    users_spec = """
openapi: 3.0.3
info:
  title: Users API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: get_users
      responses:
        '200':
          description: List of users
    post:
      operationId: create_user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: User created
  /users/{user_id}:
    get:
      operationId: get_user
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
        '404':
          description: User not found
"""
    (api_dir / "users.yaml").write_text(users_spec)

    # Create test implementation
    impl_code = """
class Implementation:
    def get_users(self, data):
        return [], 200
    
    def get_user(self, data):
        return {
            "type": "https://api.example.com/errors/user-not-found",
            "title": "User Not Found",
            "detail": "The requested user does not exist in our system",
            "status": 404,
            "instance": "/users/999"
        }, 404
    
    def create_user(self, data):
        return {"user_id": 1, "name": data["name"]}, 201
"""
    (impl_dir / "users.py").write_text(impl_code)

    # Load implementation directly
    spec = importlib.util.spec_from_file_location(
        "implementation_module", impl_dir / "users.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    implementation = module.Implementation()

    test_app = create_app(
        spec_path=api_dir / "users.yaml", implementation=implementation
    )

    client = TestClient(test_app)
    response = client.get("/users/999")

    assert response.status_code == 404
    assert response.json() == {
        "type": "https://api.example.com/errors/user-not-found",
        "title": "User Not Found",
        "detail": "The requested user does not exist in our system",
        "status": 404,
        "instance": "/users/999",
    }


def test_success_responses_not_transformed(tmp_path):
    """Test that success responses are not transformed."""
    # Create directory structure
    api_dir = tmp_path / "api"
    impl_dir = tmp_path / "implementations"
    api_dir.mkdir()
    impl_dir.mkdir()

    # Create a simple users.yaml file
    users_spec = """
openapi: 3.0.3
info:
  title: Users API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: get_users
      responses:
        '200':
          description: List of users
    post:
      operationId: create_user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        '201':
          description: User created
  /users/{user_id}:
    get:
      operationId: get_user
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
        '404':
          description: User not found
"""
    (api_dir / "users.yaml").write_text(users_spec)

    # Create test implementation
    impl_code = """
class Implementation:
    def get_users(self, data):
        return [], 200
    
    def get_user(self, data):
        return {"user_id": 1, "name": "Alice"}, 200
    
    def create_user(self, data):
        return {"user_id": 1, "name": data["name"]}, 201
"""
    (impl_dir / "users.py").write_text(impl_code)

    # Load implementation directly
    spec = importlib.util.spec_from_file_location(
        "implementation_module", impl_dir / "users.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    implementation = module.Implementation()

    test_app = create_app(
        spec_path=api_dir / "users.yaml", implementation=implementation
    )

    client = TestClient(test_app)
    response = client.get("/users/1")

    assert response.status_code == 200
    assert response.json() == {"user_id": 1, "name": "Alice"}

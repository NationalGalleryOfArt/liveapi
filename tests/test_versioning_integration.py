"""Integration tests for versioning functionality."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../examples/versioning'))

from src.automatic.app import create_app
from examples.versioning.implementation import UserImplementation
from fastapi.testclient import TestClient


class TestVersioningIntegration:
    """Integration tests for versioned API functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.impl = UserImplementation()
    
    def test_v1_create_and_get_user(self):
        """Test v1 API user creation and retrieval."""
        app = create_app("examples/versioning/users_v1.yaml", self.impl)
        client = TestClient(app)
        
        # Create user with v1 format
        create_response = client.post("/users", json={
            "name": "John",
            "email": "john@example.com"
        })
        
        assert create_response.status_code == 201
        data = create_response.json()
        assert "user_id" in data
        user_id = data["user_id"]
        
        # Get user with v1 format
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        
        user_data = get_response.json()
        assert user_data == {
            "user_id": user_id,
            "name": "John"
        }
    
    def test_v2_create_and_get_user(self):
        """Test v2 API user creation and retrieval."""
        app = create_app("examples/versioning/users_v2.yaml", self.impl)
        client = TestClient(app)
        
        # Create user with v2 format
        create_response = client.post("/users", json={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1234567890"
        })
        
        assert create_response.status_code == 201
        data = create_response.json()
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == "jane@example.com"
        user_id = data["user_id"]
        
        # Get user with v2 format
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        
        user_data = get_response.json()
        assert user_data == {
            "user_id": user_id,
            "full_name": "Jane Doe",
            "email": "jane@example.com"
        }
    
    def test_v3_get_user(self):
        """Test v3 API user retrieval with nested profile."""
        app = create_app("examples/versioning/users_v3.yaml", self.impl)
        client = TestClient(app)
        
        # Use existing user (created in setup)
        user_id = 1
        
        # Get user with v3 format
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        
        user_data = get_response.json()
        assert "user_id" in user_data
        assert "profile" in user_data
        assert "full_name" in user_data["profile"]
        assert "email" in user_data["profile"]
        assert "preferences" in user_data["profile"]
    
    def test_version_compatibility_same_implementation(self):
        """Test that different versions work with the same implementation."""
        # Create apps for different versions using the same implementation
        app_v1 = create_app("examples/versioning/users_v1.yaml", self.impl)
        app_v2 = create_app("examples/versioning/users_v2.yaml", self.impl)
        app_v3 = create_app("examples/versioning/users_v3.yaml", self.impl)
        
        client_v1 = TestClient(app_v1)
        client_v2 = TestClient(app_v2)
        client_v3 = TestClient(app_v3)
        
        # Create user with v1
        create_v1 = client_v1.post("/users", json={"name": "TestUser", "email": "test@example.com"})
        assert create_v1.status_code == 201
        user_id = create_v1.json()["user_id"]
        
        # Get same user with different versions
        get_v1 = client_v1.get(f"/users/{user_id}")
        get_v2 = client_v2.get(f"/users/{user_id}")
        get_v3 = client_v3.get(f"/users/{user_id}")
        
        assert get_v1.status_code == 200
        assert get_v2.status_code == 200
        assert get_v3.status_code == 200
        
        # Verify different response formats
        v1_data = get_v1.json()
        v2_data = get_v2.json()
        v3_data = get_v3.json()
        
        # v1 format: simple
        assert "name" in v1_data
        assert "full_name" not in v1_data
        
        # v2 format: enhanced
        assert "full_name" in v2_data
        assert "email" in v2_data
        assert "profile" not in v2_data
        
        # v3 format: nested
        assert "profile" in v3_data
        assert "full_name" in v3_data["profile"]
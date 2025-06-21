"""Integration tests for versioning functionality."""

import sys
import os
from src.automatic.app import create_app
from examples.versioning.implementation import UserImplementation
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../examples/versioning"))


class TestVersioningIntegration:
    """Integration tests for versioned API functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.impl = UserImplementation()

    def test_v1_create_and_get_user(self, tmp_path):
        """Test v1 API user creation and retrieval."""
        # Create directory structure
        api_dir = tmp_path / "api"
        impl_dir = tmp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()

        # Copy spec and create implementation wrapper
        import shutil

        shutil.copy("examples/versioning/users_v1.yaml", api_dir / "users_v1.yaml")

        # Create wrapper implementation that imports UserImplementation as Implementation
        impl_code = """
from examples.versioning.implementation import UserImplementation as Implementation
"""
        (impl_dir / "users_v1.py").write_text(impl_code)

        app = create_app(api_dir=api_dir, impl_dir=impl_dir)
        client = TestClient(app)

        # Create user with v1 format (with prefix)
        create_response = client.post(
            "/users_v1/users", json={"name": "John", "email": "john@example.com"}
        )

        assert create_response.status_code == 201
        data = create_response.json()
        assert "user_id" in data
        user_id = data["user_id"]

        # Get user with v1 format (with prefix)
        get_response = client.get(f"/users_v1/users/{user_id}")
        assert get_response.status_code == 200

        user_data = get_response.json()
        assert user_data == {"user_id": user_id, "name": "John"}

    def test_v2_create_and_get_user(self, tmp_path):
        """Test v2 API user creation and retrieval."""
        # Create directory structure
        api_dir = tmp_path / "api"
        impl_dir = tmp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()

        # Copy spec and create implementation wrapper
        import shutil

        shutil.copy("examples/versioning/users_v2.yaml", api_dir / "users_v2.yaml")

        # Create wrapper implementation that imports UserImplementation as Implementation
        impl_code = """
from examples.versioning.implementation import UserImplementation as Implementation
"""
        (impl_dir / "users_v2.py").write_text(impl_code)

        app = create_app(api_dir=api_dir, impl_dir=impl_dir)
        client = TestClient(app)

        # Create user with v2 format (with prefix)
        create_response = client.post(
            "/users_v2/users",
            json={
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1234567890",
            },
        )

        assert create_response.status_code == 201
        data = create_response.json()
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == "jane@example.com"
        user_id = data["user_id"]

        # Get user with v2 format (with prefix)
        get_response = client.get(f"/users_v2/users/{user_id}")
        assert get_response.status_code == 200

        user_data = get_response.json()
        assert user_data == {
            "user_id": user_id,
            "full_name": "Jane Doe",
            "email": "jane@example.com",
        }

    def test_v3_get_user(self, tmp_path):
        """Test v3 API user retrieval with nested profile."""
        # Create directory structure
        api_dir = tmp_path / "api"
        impl_dir = tmp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()

        # Copy spec and create implementation wrapper
        import shutil

        shutil.copy("examples/versioning/users_v3.yaml", api_dir / "users_v3.yaml")

        # Create wrapper implementation that imports UserImplementation as Implementation
        impl_code = """
from examples.versioning.implementation import UserImplementation as Implementation
"""
        (impl_dir / "users_v3.py").write_text(impl_code)

        app = create_app(api_dir=api_dir, impl_dir=impl_dir)
        client = TestClient(app)

        # Use existing user (created in setup)
        user_id = 1

        # Get user with v3 format (with prefix)
        get_response = client.get(f"/users_v3/users/{user_id}")
        assert get_response.status_code == 200

        user_data = get_response.json()
        assert "user_id" in user_data
        assert "profile" in user_data
        assert "full_name" in user_data["profile"]
        assert "email" in user_data["profile"]
        assert "preferences" in user_data["profile"]

    def test_version_compatibility_same_implementation(self, tmp_path):
        """Test that different versions work with the same implementation."""
        # Create directory structure
        api_dir = tmp_path / "api"
        impl_dir = tmp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()

        # Copy all version specs and create implementation wrappers
        import shutil

        shutil.copy("examples/versioning/users_v1.yaml", api_dir / "users_v1.yaml")
        shutil.copy("examples/versioning/users_v2.yaml", api_dir / "users_v2.yaml")
        shutil.copy("examples/versioning/users_v3.yaml", api_dir / "users_v3.yaml")

        # Create wrapper implementations
        impl_code = """
from examples.versioning.implementation import UserImplementation as Implementation
"""
        (impl_dir / "users_v1.py").write_text(impl_code)
        (impl_dir / "users_v2.py").write_text(impl_code)
        (impl_dir / "users_v3.py").write_text(impl_code)

        # Create a single app with all versions
        app = create_app(api_dir=api_dir, impl_dir=impl_dir)

        client = TestClient(app)

        # Create user with v1 (with prefix)
        create_v1 = client.post(
            "/users_v1/users", json={"name": "TestUser", "email": "test@example.com"}
        )
        assert create_v1.status_code == 201
        user_id = create_v1.json()["user_id"]

        # Get user with v1 (same implementation instance)
        get_v1 = client.get(f"/users_v1/users/{user_id}")
        assert get_v1.status_code == 200

        # Create users in v2 and v3 to test format differences
        create_v2 = client.post(
            "/users_v2/users",
            json={
                "full_name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "+1234567890",
            },
        )
        assert create_v2.status_code == 201
        user_id_v2 = create_v2.json()["user_id"]

        get_v2 = client.get(f"/users_v2/users/{user_id_v2}")
        assert get_v2.status_code == 200

        # For v3, we'll use the predefined user ID 1 from the mock data
        get_v3 = client.get("/users_v3/users/1")
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

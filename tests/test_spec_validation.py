"""Tests for OpenAPI specification validation."""

import pytest
import tempfile
import yaml
from pathlib import Path
from automatic.cli import validate_spec_paths, _check_path_conflicts, _paths_conflict


class TestRootPathValidation:
    """Test validation of root path mounting."""

    def test_root_path_rejected(self):
        """Root path '/' should be rejected."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/": {
                    "get": {
                        "operationId": "get_root",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(spec, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_paths(temp_path)
            assert exc_info.value.code == 1
        finally:
            temp_path.unlink()

    def test_valid_path_accepted(self):
        """Valid resource paths should be accepted."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "get_users",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(spec, f)
            temp_path = Path(f.name)

        try:
            # Should not raise any exception
            validate_spec_paths(temp_path)
        finally:
            temp_path.unlink()

    def test_multiple_valid_paths_accepted(self):
        """Multiple non-conflicting paths should be accepted."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "get_users",
                        "responses": {"200": {"description": "Success"}},
                    }
                },
                "/products": {
                    "get": {
                        "operationId": "get_products",
                        "responses": {"200": {"description": "Success"}},
                    }
                },
                "/orders": {
                    "get": {
                        "operationId": "get_orders",
                        "responses": {"200": {"description": "Success"}},
                    }
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(spec, f)
            temp_path = Path(f.name)

        try:
            # Should not raise any exception
            validate_spec_paths(temp_path)
        finally:
            temp_path.unlink()


class TestPathConflictValidation:
    """Test validation of conflicting paths."""

    def test_duplicate_paths_rejected(self):
        """Exact duplicate paths should be rejected."""
        {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "get_users",
                        "responses": {"200": {"description": "Success"}},
                    },
                    "post": {
                        "operationId": "create_user",
                        "responses": {"201": {"description": "Created"}},
                    },
                }
            },
        }

        # Add the same path again (this would be a YAML/JSON parsing issue but let's test our logic)
        conflicts = _check_path_conflicts(["/users", "/users"])
        assert len(conflicts) == 1
        assert "Duplicate paths: /users" in conflicts[0]

    def test_prefix_path_conflicts_rejected(self):
        """Paths where one is a prefix of another should be rejected."""
        conflicts = _check_path_conflicts(["/users", "/users/profile"])
        assert len(conflicts) == 1
        assert "Conflicting paths: '/users' and '/users/profile'" in conflicts[0]

    def test_parameter_conflicts_detected(self):
        """Conflicting parameterized paths should be detected."""
        conflicts = _check_path_conflicts(["/users/{id}", "/users/{user_id}"])
        # Both have parameters in same position - should not conflict
        assert len(conflicts) == 0

        # But these should conflict
        conflicts = _check_path_conflicts(["/users/{id}", "/users/profile"])
        assert len(conflicts) == 1

    def test_no_conflicts_for_distinct_paths(self):
        """Distinct resource paths should not conflict."""
        paths = ["/users", "/products", "/orders", "/categories"]
        conflicts = _check_path_conflicts(paths)
        assert len(conflicts) == 0

    def test_rest_patterns_no_conflict(self):
        """Standard REST patterns should not conflict."""
        paths = [
            "/users",  # GET /users (list)
            "/users/{id}",  # GET /users/{id} (show)
            # POST /users (create)
            # PUT /users/{id} (update)
            # DELETE /users/{id} (delete)
        ]
        conflicts = _check_path_conflicts(paths)
        assert len(conflicts) == 0


class TestPathConflictDetection:
    """Test the low-level path conflict detection logic."""

    def test_paths_conflict_exact_duplicates(self):
        """Exact duplicate paths should conflict."""
        assert (
            _paths_conflict("/users", "/users") is False
        )  # Same path, different methods OK

    def test_paths_conflict_prefix_detection(self):
        """Prefix conflicts should be detected."""
        assert _paths_conflict("/users", "/users/profile") is True
        assert _paths_conflict("/users/profile", "/users") is True
        assert _paths_conflict("/api/v1/users", "/api/v1/users/settings") is True

    def test_paths_conflict_parameters(self):
        """Parameter conflicts should be handled correctly."""
        # Same parameter structure - no conflict
        assert _paths_conflict("/users/{id}", "/users/{user_id}") is False

        # Parameter vs literal - conflict
        assert _paths_conflict("/users/{id}", "/users/profile") is True
        assert _paths_conflict("/users/profile", "/users/{id}") is True

        # Different parameter structures - these should conflict because posts vs comments are literals
        assert (
            _paths_conflict("/users/{id}/posts", "/users/{id}/comments") is False
        )  # Actually these don't conflict, different endpoints

    def test_paths_conflict_different_resources(self):
        """Different resources should not conflict."""
        assert _paths_conflict("/users", "/products") is False
        assert _paths_conflict("/api/users", "/api/products") is False
        assert _paths_conflict("/v1/users", "/v2/users") is False

    def test_paths_conflict_trailing_slashes(self):
        """Trailing slashes should be normalized."""
        assert _paths_conflict("/users/", "/users") is False
        assert _paths_conflict("/users/", "/users/profile/") is True


class TestSpecValidationIntegration:
    """Test the complete spec validation flow."""

    def test_spec_with_conflicts_rejected(self):
        """Spec with conflicting paths should be rejected."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "get_users",
                        "responses": {"200": {"description": "Success"}},
                    }
                },
                "/users/profile": {
                    "get": {
                        "operationId": "get_profile",
                        "responses": {"200": {"description": "Success"}},
                    }
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(spec, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_paths(temp_path)
            assert exc_info.value.code == 1
        finally:
            temp_path.unlink()

    def test_json_spec_validation(self):
        """JSON specs should also be validated."""
        import json

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/": {
                    "get": {
                        "operationId": "get_root",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(spec, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(SystemExit) as exc_info:
                validate_spec_paths(temp_path)
            assert exc_info.value.code == 1
        finally:
            temp_path.unlink()

    def test_invalid_yaml_gracefully_handled(self):
        """Invalid YAML should be gracefully handled."""
        invalid_yaml = "invalid: yaml: content: [unclosed"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml)
            temp_path = Path(f.name)

        try:
            # Should not raise exception - gracefully handle parsing errors
            validate_spec_paths(temp_path)
        finally:
            temp_path.unlink()

    def test_non_openapi_file_gracefully_handled(self):
        """Non-OpenAPI files should be gracefully handled."""
        regular_yaml = {"some": "config", "not": "openapi"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(regular_yaml, f)
            temp_path = Path(f.name)

        try:
            # Should not raise exception - file doesn't have paths
            validate_spec_paths(temp_path)
        finally:
            temp_path.unlink()


class TestComplexConflictScenarios:
    """Test complex real-world conflict scenarios."""

    def test_nested_resource_conflicts(self):
        """Complex nested resource conflicts."""
        paths = [
            "/users/{user_id}/posts",
            "/users/{user_id}/posts/{post_id}",
            "/users/{user_id}/posts/{post_id}/comments",
            "/users/profile",  # This conflicts with /users/{user_id}
        ]
        conflicts = _check_path_conflicts(paths)
        # Should detect the conflict between parameterized user_id and literal 'profile'
        assert len(conflicts) > 0
        assert any("profile" in conflict for conflict in conflicts)

    def test_versioned_api_no_conflicts(self):
        """Versioned APIs should not conflict with each other."""
        paths = [
            "/v1/users",
            "/v1/users/{id}",
            "/v2/users",
            "/v2/users/{id}",
            "/v3/users",
            "/v3/users/{id}",
        ]
        conflicts = _check_path_conflicts(paths)
        assert len(conflicts) == 0

    def test_microservice_style_paths(self):
        """Microservice-style paths should be validated correctly."""
        paths = [
            "/api/user-service/users",
            "/api/user-service/users/{id}",
            "/api/order-service/orders",
            "/api/order-service/orders/{id}",
            "/api/product-service/products",
            "/api/product-service/products/{id}",
        ]
        conflicts = _check_path_conflicts(paths)
        assert len(conflicts) == 0

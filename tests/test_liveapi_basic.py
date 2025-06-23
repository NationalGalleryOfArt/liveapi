"""Basic tests for liveapi change detection."""

import pytest
import tempfile
import yaml
import json
from pathlib import Path

from liveapi.metadata_manager import MetadataManager, ProjectStatus
from liveapi.change_detector import ChangeDetector, ChangeType


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification."""
    return {
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
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        },
                    },
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/users/{user_id}": {
                "get": {
                    "operationId": "get_user",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                    },
                }
            }
        },
    }


class TestMetadataManager:
    """Test metadata management functionality."""

    def test_initialize_project(self, temp_project):
        """Test project initialization."""
        # Change to temp directory
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            metadata_manager = MetadataManager()

            # Initially uninitialized
            assert metadata_manager.get_project_status() == ProjectStatus.UNINITIALIZED

            # Initialize project
            config = metadata_manager.initialize_project("test-project")

            # Check initialization
            assert metadata_manager.get_project_status() == ProjectStatus.INITIALIZED
            assert config.project_name == "test-project"
            assert (temp_project / ".liveapi").exists()
            assert (temp_project / ".liveapi" / "config.json").exists()

        finally:
            os.chdir(original_cwd)

    def test_spec_checksum_tracking(self, temp_project, sample_openapi_spec):
        """Test specification checksum tracking."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            # Create a spec file
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Initially should detect as changed (new)
            assert metadata_manager.has_spec_changed(spec_file) is True

            # Track the spec
            change_detector = ChangeDetector()
            change_detector.update_spec_tracking(spec_file)

            # Now should not detect as changed
            assert metadata_manager.has_spec_changed(spec_file) is False

            # Modify the spec
            sample_openapi_spec["info"]["version"] = "2.0.0"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Should detect change
            assert metadata_manager.has_spec_changed(spec_file) is True

        finally:
            os.chdir(original_cwd)


class TestChangeDetector:
    """Test change detection functionality."""

    def test_find_api_specs(self, temp_project, sample_openapi_spec):
        """Test API specification discovery."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            change_detector = ChangeDetector()

            # No specs initially
            specs = change_detector.find_api_specs()
            assert len(specs) == 0

            # Create specifications directory with specs
            specs_dir = temp_project / "specifications"
            specs_dir.mkdir()

            spec1 = specs_dir / "users.yaml"
            spec2 = specs_dir / "orders.yml"
            spec3 = specs_dir / "products.json"

            with open(spec1, "w") as f:
                yaml.dump(sample_openapi_spec, f)
            with open(spec2, "w") as f:
                yaml.dump(sample_openapi_spec, f)
            with open(spec3, "w") as f:
                json.dump(sample_openapi_spec, f)

            # Should find all specs
            specs = change_detector.find_api_specs()
            assert len(specs) == 3

            spec_names = [s.name for s in specs]
            assert "users.yaml" in spec_names
            assert "orders.yml" in spec_names
            assert "products.json" in spec_names

        finally:
            os.chdir(original_cwd)

    def test_detect_new_spec(self, temp_project, sample_openapi_spec):
        """Test detection of new specifications."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            change_detector = ChangeDetector()

            # Create a new spec file
            spec_file = temp_project / "new_api.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Should detect as new
            analysis = change_detector.detect_changes(spec_file)
            assert analysis is not None
            assert len(analysis.changes) == 1
            assert analysis.changes[0].change_type == ChangeType.NEW
            assert not analysis.is_breaking

        finally:
            os.chdir(original_cwd)

    def test_detect_version_changes(self, temp_project, sample_openapi_spec):
        """Test detection of version changes."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize and track initial spec
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            change_detector = ChangeDetector()

            spec_file = temp_project / "api.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Track initial version
            change_detector.update_spec_tracking(spec_file)

            # Update to minor version
            sample_openapi_spec["info"]["version"] = "1.1.0"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Should detect non-breaking version change
            analysis = change_detector.detect_changes(spec_file)
            assert analysis is not None
            assert any("Version changed" in c.description for c in analysis.changes)
            assert not analysis.is_breaking  # Minor version bump

            # Update to major version
            sample_openapi_spec["info"]["version"] = "2.0.0"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Update tracking with minor version first
            change_detector.update_spec_tracking(spec_file)

            # Now test major version change
            sample_openapi_spec["info"]["version"] = "3.0.0"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            analysis = change_detector.detect_changes(spec_file)
            assert analysis is not None
            version_changes = [
                c for c in analysis.changes if "Version changed" in c.description
            ]
            assert len(version_changes) > 0
            assert any(c.is_breaking for c in version_changes)  # Major version bump

        finally:
            os.chdir(original_cwd)

    def test_detect_path_changes(self, temp_project, sample_openapi_spec):
        """Test detection of path changes."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize and track initial spec
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            change_detector = ChangeDetector()

            spec_file = temp_project / "api.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            change_detector.update_spec_tracking(spec_file)

            # Add new endpoint (non-breaking)
            sample_openapi_spec["paths"]["/health"] = {
                "get": {
                    "operationId": "health_check",
                    "responses": {"200": {"description": "Health status"}},
                }
            }

            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            analysis = change_detector.detect_changes(spec_file)
            assert analysis is not None

            # Should have changes but not breaking
            path_additions = [
                c
                for c in analysis.changes
                if c.change_type == ChangeType.NEW and "endpoint" in c.description
            ]
            assert len(path_additions) > 0
            assert not any(c.is_breaking for c in path_additions)

            # Remove existing endpoint (breaking)
            change_detector.update_spec_tracking(spec_file)  # Update tracking
            del sample_openapi_spec["paths"]["/users"]

            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            analysis = change_detector.detect_changes(spec_file)
            assert analysis is not None

            path_deletions = [
                c
                for c in analysis.changes
                if c.change_type == ChangeType.DELETED and "endpoint" in c.description
            ]
            assert len(path_deletions) > 0
            assert all(c.is_breaking for c in path_deletions)

        finally:
            os.chdir(original_cwd)

"""Tests for liveapi version management system."""

import pytest
import tempfile
import yaml
from pathlib import Path

from liveapi.version_manager import VersionManager, VersionType, Version
from liveapi.metadata_manager import MetadataManager


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
        "info": {"title": "Users API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "get_users",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
    }


class TestVersion:
    """Test Version class functionality."""

    def test_version_parsing(self):
        """Test version string parsing."""
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert str(v) == "1.2.3"

    def test_version_parsing_invalid(self):
        """Test invalid version string parsing."""
        with pytest.raises(ValueError):
            Version.parse("1.2")

        with pytest.raises(ValueError):
            Version.parse("invalid")

    def test_version_bumping(self):
        """Test version bumping functionality."""
        v = Version(1, 2, 3)

        # Major bump
        major = v.bump(VersionType.MAJOR)
        assert str(major) == "2.0.0"

        # Minor bump
        minor = v.bump(VersionType.MINOR)
        assert str(minor) == "1.3.0"

        # Patch bump
        patch_version = v.bump(VersionType.PATCH)
        assert str(patch_version) == "1.2.4"


class TestVersionManager:
    """Test VersionManager functionality."""

    def test_extract_spec_name(self, temp_project):
        """Test specification name extraction."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            version_manager = VersionManager()

            # Test normal filename
            assert version_manager._extract_spec_name(Path("users.yaml")) == "users"

            # Test versioned filename
            assert (
                version_manager._extract_spec_name(Path("users_v1.0.0.yaml")) == "users"
            )

            # Test complex name
            assert (
                version_manager._extract_spec_name(Path("user_management_api.yaml"))
                == "user_management_api"
            )

        finally:
            os.chdir(original_cwd)

    def test_create_first_version(self, temp_project, sample_openapi_spec):
        """Test creating the first version of a specification."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            version_manager = VersionManager()

            # Create initial spec file
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create first version
            versioned_spec = version_manager.create_version(
                spec_file, VersionType.MAJOR
            )

            assert versioned_spec.name == "users"
            assert str(versioned_spec.version) == "1.0.0"
            assert versioned_spec.file_path.name == "users_v1.0.0.yaml"
            assert versioned_spec.file_path.exists()

            # Check that specifications directory was created
            specs_dir = temp_project / "specifications"
            assert specs_dir.exists()
            assert (specs_dir / "users_v1.0.0.yaml").exists()

            # Check that latest symlink was created
            latest_dir = specs_dir / "latest"
            assert latest_dir.exists()
            assert (latest_dir / "users.yaml").exists()
            assert (latest_dir / "users.yaml").is_symlink()

        finally:
            os.chdir(original_cwd)

    def test_create_subsequent_versions(self, temp_project, sample_openapi_spec):
        """Test creating subsequent versions."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            version_manager = VersionManager()

            # Create initial spec file
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create first version
            v1 = version_manager.create_version(spec_file, VersionType.MAJOR)
            assert str(v1.version) == "1.0.0"

            # Modify spec for next version
            sample_openapi_spec["paths"]["/users/{id}"] = {
                "get": {
                    "operationId": "get_user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            }
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create minor version
            v2 = version_manager.create_version(spec_file, VersionType.MINOR)
            assert str(v2.version) == "1.1.0"

            # Create patch version
            v3 = version_manager.create_version(spec_file, VersionType.PATCH)
            assert str(v3.version) == "1.1.1"

            # Check that all versions exist
            versions = version_manager.get_spec_versions("users")
            assert len(versions) == 3
            assert [str(v.version) for v in versions] == ["1.0.0", "1.1.0", "1.1.1"]

            # Check latest version
            latest = version_manager.get_latest_version("users")
            assert str(latest.version) == "1.1.1"

        finally:
            os.chdir(original_cwd)

    def test_create_target_version(self, temp_project, sample_openapi_spec):
        """Test creating a specific target version."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            version_manager = VersionManager()

            # Create initial spec file
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create specific version
            versioned_spec = version_manager.create_version(
                spec_file, target_version="2.5.1"
            )

            assert str(versioned_spec.version) == "2.5.1"
            assert versioned_spec.file_path.name == "users_v2.5.1.yaml"

        finally:
            os.chdir(original_cwd)

    def test_version_comparison(self, temp_project, sample_openapi_spec):
        """Test version comparison functionality."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            version_manager = VersionManager()

            # Create initial spec file
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create first version
            _ = version_manager.create_version(spec_file, VersionType.MAJOR)

            # Modify spec significantly
            sample_openapi_spec["info"]["version"] = "2.0.0"
            sample_openapi_spec["paths"]["/users/{id}"] = {
                "get": {
                    "operationId": "get_user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Success"}},
                }
            }
            # Remove an endpoint (breaking change)
            del sample_openapi_spec["paths"]["/users"]

            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create second version
            _ = version_manager.create_version(spec_file, VersionType.MAJOR)

            # Compare versions
            analysis = version_manager.compare_versions("users", "1.0.0", "2.0.0")

            assert analysis is not None
            assert analysis.is_breaking  # Should detect breaking changes
            assert len(analysis.changes) > 0

            # Should detect removed endpoint
            removed_changes = [
                c for c in analysis.changes if "removed" in c.description.lower()
            ]
            assert len(removed_changes) > 0

        finally:
            os.chdir(original_cwd)

    def test_migration_plan_generation(self, temp_project, sample_openapi_spec):
        """Test migration plan generation."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            version_manager = VersionManager()

            # Create initial spec file
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create first version
            _ = version_manager.create_version(spec_file, VersionType.MAJOR)

            # Create breaking changes
            del sample_openapi_spec["paths"]["/users"]  # Remove endpoint
            sample_openapi_spec["info"]["version"] = "2.0.0"

            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create second version
            _ = version_manager.create_version(spec_file, VersionType.MAJOR)

            # Generate migration plan
            migration_plan = version_manager.generate_migration_plan(
                "users", "1.0.0", "2.0.0"
            )

            assert migration_plan.from_version == Version(1, 0, 0)
            assert migration_plan.to_version == Version(2, 0, 0)
            assert len(migration_plan.breaking_changes) > 0
            assert len(migration_plan.migration_steps) > 0
            assert migration_plan.requires_manual_intervention is True
            assert migration_plan.estimated_effort in ["low", "medium", "high"]

        finally:
            os.chdir(original_cwd)

    def test_compatibility_matrix(self, temp_project, sample_openapi_spec):
        """Test compatibility matrix generation."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            version_manager = VersionManager()

            # Create initial spec file
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(sample_openapi_spec, f)

            # Create multiple versions
            _ = version_manager.create_version(spec_file, VersionType.MAJOR)
            _ = version_manager.create_version(spec_file, VersionType.MINOR)
            _ = version_manager.create_version(spec_file, VersionType.MAJOR)

            # Get compatibility matrix
            matrix = version_manager.get_compatibility_matrix()

            assert "users" in matrix
            user_versions = matrix["users"]

            # Should have all three versions
            assert "1.0.0" in user_versions
            assert "1.1.0" in user_versions
            assert "2.0.0" in user_versions

            # Latest should be marked
            assert user_versions["2.0.0"]["is_latest"] is True
            assert user_versions["1.0.0"]["is_latest"] is False

            # Major version should have breaking changes
            assert user_versions["2.0.0"]["has_breaking_changes"] is True
            assert user_versions["1.0.0"]["has_breaking_changes"] is False

        finally:
            os.chdir(original_cwd)

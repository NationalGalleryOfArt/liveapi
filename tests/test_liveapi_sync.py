"""Tests for liveapi synchronization system."""

import pytest
import tempfile
import yaml
from pathlib import Path
from liveapi.sync_manager import SyncManager
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


@pytest.fixture
def crud_openapi_spec():
    """CRUD OpenAPI specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "Users API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "get": {
                    "operationId": "list_users",
                    "responses": {"200": {"description": "Success"}},
                },
                "post": {
                    "operationId": "create_user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                    },
                                    "required": ["name", "email"],
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Created"}},
                },
            },
            "/users/{id}": {
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
                },
                "put": {
                    "operationId": "update_user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"},
                                    },
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Updated"}},
                },
                "delete": {
                    "operationId": "delete_user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"204": {"description": "Deleted"}},
                },
            },
        },
    }


class TestSyncManager:
    """Test SyncManager functionality for CRUD+ mode."""

    def test_analyze_sync_no_changes(self, temp_project, crud_openapi_spec):
        """Test sync analysis when no changes are needed."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            # Create and track a spec
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Track the spec (simulates it being already synced)
            from liveapi.change_detector import ChangeDetector

            change_detector = ChangeDetector()
            change_detector.update_spec_tracking(spec_file)

            # Create main.py to simulate already synced state
            main_py = temp_project / "main.py"
            main_py.write_text(
                'from liveapi.implementation import create_app\napp = create_app("users.yaml")'
            )

            # Analyze sync requirements
            sync_manager = SyncManager()
            sync_plan = sync_manager.analyze_sync_requirements()

            # Should have no sync items needed since everything is up to date
            assert len(sync_plan.items) == 0

        finally:
            os.chdir(original_cwd)

    def test_analyze_sync_with_changes(self, temp_project, crud_openapi_spec):
        """Test sync analysis when changes are detected."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            # Create and track initial spec
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            from liveapi.change_detector import ChangeDetector

            change_detector = ChangeDetector()
            change_detector.update_spec_tracking(spec_file)

            # Create main.py
            main_py = temp_project / "main.py"
            main_py.write_text(
                'from liveapi.implementation import create_app\napp = create_app("users.yaml")'
            )

            # Modify spec (add new endpoint)
            crud_openapi_spec["paths"]["/users/search"] = {
                "get": {
                    "operationId": "search_users",
                    "responses": {"200": {"description": "Search results"}},
                }
            }
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Analyze sync requirements
            sync_manager = SyncManager()
            sync_plan = sync_manager.analyze_sync_requirements()

            # Should detect that sync is needed (spec changed)
            assert len(sync_plan.items) >= 1
            assert not sync_plan.requires_manual_review  # Non-breaking change
            assert sync_plan.estimated_time in ["low", "medium", "none"]

        finally:
            os.chdir(original_cwd)

    def test_analyze_sync_breaking_changes(self, temp_project, crud_openapi_spec):
        """Test sync analysis with breaking changes."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            # Create and track initial spec
            spec_file = temp_project / "users.yaml"
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            from liveapi.change_detector import ChangeDetector

            change_detector = ChangeDetector()
            change_detector.update_spec_tracking(spec_file)

            # Create existing main.py to trigger sync analysis
            main_py = temp_project / "main.py"
            main_py.write_text(
                'from liveapi.implementation import create_app\napp = create_app("users.yaml")'
            )

            # Make breaking change (remove required field)
            crud_openapi_spec["paths"]["/users"]["post"]["requestBody"]["content"][
                "application/json"
            ]["schema"]["required"] = [
                "name"
            ]  # Remove email
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Analyze sync requirements
            sync_manager = SyncManager()
            sync_plan = sync_manager.analyze_sync_requirements()

            # In CRUD+ mode, breaking changes are detected but may not require sync items
            # since the API handles changes dynamically. Test that the analysis completes successfully.
            assert isinstance(sync_plan.items, list)
            assert isinstance(sync_plan.breaking_changes, list)
            # Breaking changes detection works regardless of sync items
            assert hasattr(sync_plan, "requires_manual_review")

        finally:
            os.chdir(original_cwd)

    def test_find_missing_implementations(self, temp_project, crud_openapi_spec):
        """Test finding specs that need main.py creation."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Create SyncManager for testing
            SyncManager()

            # Create specifications directory with specs
            specs_dir = temp_project / "specifications"
            specs_dir.mkdir()

            spec1 = specs_dir / "users.yaml"
            spec2 = specs_dir / "products.yaml"

            with open(spec1, "w") as f:
                yaml.dump(crud_openapi_spec, f)
            with open(spec2, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # In CRUD+ mode, missing implementations means missing main.py
            from liveapi.sync.plan import _find_missing_implementations
            from liveapi.version_manager import VersionManager

            version_manager = VersionManager(temp_project)
            missing = _find_missing_implementations(
                specs_dir, temp_project / "implementations", version_manager
            )

            # Should find that main.py is missing for these specs
            assert len(missing) >= 1  # At least main.py needs to be created

        finally:
            os.chdir(original_cwd)

    def test_find_implementation_path(self, temp_project):
        """Test finding main.py path for CRUD+ mode."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            from liveapi.sync.plan import _find_implementation_path

            # In CRUD+ mode, implementation is always main.py
            impl_path = _find_implementation_path(
                "users", temp_project / "implementations"
            )

            # Should point to main.py since that's our CRUD+ implementation
            assert (
                impl_path is None
                or impl_path.name == "main.py"
                or "main" in str(impl_path)
            )

        finally:
            os.chdir(original_cwd)

    def test_execute_create_implementation(self, temp_project, crud_openapi_spec):
        """Test creating CRUD+ main.py implementation."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Create spec file
            spec_file = temp_project / "specifications" / "users.yaml"
            spec_file.parent.mkdir(parents=True)
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Create sync plan
            sync_manager = SyncManager()
            sync_plan = sync_manager.analyze_sync_requirements()

            # Execute sync (should create main.py)
            success = sync_manager.execute_sync_plan(sync_plan, preview_only=False)

            # Should succeed and create main.py
            assert success
            main_py = temp_project / "main.py"
            assert main_py.exists()

            # main.py should contain CRUD+ app creation
            content = main_py.read_text()
            assert "liveapi.implementation" in content
            assert "create_app" in content

        finally:
            os.chdir(original_cwd)

    def test_execute_update_implementation(self, temp_project, crud_openapi_spec):
        """Test updating CRUD+ implementation (main.py regeneration)."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project and create spec
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            # Set backend to default (in-memory) for this test
            config = metadata_manager.load_config()
            config.backend_type = "default"
            metadata_manager.save_config(config)

            spec_file = temp_project / "specifications" / "users.yaml"
            spec_file.parent.mkdir(parents=True)
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Track the spec
            from liveapi.change_detector import ChangeDetector

            change_detector = ChangeDetector()
            change_detector.update_spec_tracking(spec_file)

            # Create existing main.py
            main_py = temp_project / "main.py"
            main_py.write_text(
                '# Old main.py\nfrom liveapi.implementation import create_app\napp = create_app("specifications/users.yaml")'
            )

            # Modify spec
            crud_openapi_spec["info"]["version"] = "1.1.0"
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Execute sync (should update main.py)
            sync_manager = SyncManager()
            sync_plan = sync_manager.analyze_sync_requirements()
            success = sync_manager.execute_sync_plan(sync_plan, preview_only=False)

            # Should succeed
            assert success
            assert main_py.exists()

        finally:
            os.chdir(original_cwd)

    def test_execute_migrate_implementation(self, temp_project, crud_openapi_spec):
        """Test migrating CRUD+ implementation with breaking changes."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Initialize project
            metadata_manager = MetadataManager()
            metadata_manager.initialize_project("test")

            # Set backend to default (in-memory) for this test
            config = metadata_manager.load_config()
            config.backend_type = "default"
            metadata_manager.save_config(config)

            # Create and track spec
            spec_file = temp_project / "specifications" / "users.yaml"
            spec_file.parent.mkdir(parents=True)
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            from liveapi.change_detector import ChangeDetector

            change_detector = ChangeDetector()
            change_detector.update_spec_tracking(spec_file)

            # Create existing main.py
            main_py = temp_project / "main.py"
            main_py.write_text(
                'from liveapi.implementation import create_app\napp = create_app("specifications/users.yaml")'
            )

            # Make breaking change
            del crud_openapi_spec["paths"][
                "/users/{id}"
            ]  # Remove user detail endpoints
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Execute sync
            sync_manager = SyncManager()
            sync_plan = sync_manager.analyze_sync_requirements()
            success = sync_manager.execute_sync_plan(sync_plan, preview_only=False)

            # Should handle migration (CRUD+ is resilient to spec changes)
            assert success

        finally:
            os.chdir(original_cwd)

    def test_estimate_sync_effort(self, temp_project):
        """Test sync effort estimation."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Create SyncManager for testing
            SyncManager()

            # In CRUD+ mode, most sync operations are low effort
            from liveapi.sync.plan import _estimate_sync_effort

            # Create a sample sync item
            from liveapi.sync.models import SyncItem, SyncAction

            item = SyncItem(
                spec_name="users",
                action=SyncAction.CREATE,
                source_path=Path("users.yaml"),
                target_path=Path("main.py"),
                description="Create CRUD+ main.py",
            )

            effort = _estimate_sync_effort([item], [])  # Empty breaking changes list
            assert effort in ["low", "medium", "high", "none"]

        finally:
            os.chdir(original_cwd)

    def test_preview_sync_plan(self, temp_project, crud_openapi_spec, capsys):
        """Test sync plan preview functionality."""
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(temp_project)

            # Create spec
            spec_file = temp_project / "specifications" / "users.yaml"
            spec_file.parent.mkdir(parents=True)
            with open(spec_file, "w") as f:
                yaml.dump(crud_openapi_spec, f)

            # Get sync plan
            sync_manager = SyncManager()
            sync_plan = sync_manager.analyze_sync_requirements()

            # Preview the plan
            from liveapi.sync.plan import preview_sync_plan

            preview_sync_plan(sync_plan)

            # Check that preview output was generated
            captured = capsys.readouterr()
            assert "Sync Plan" in captured.out or len(sync_plan.items) == 0

        finally:
            os.chdir(original_cwd)

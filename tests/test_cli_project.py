"""Tests for cli/commands/project.py module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.liveapi.cli.commands.project import (
    handle_no_command,
    cmd_init,
    cmd_status,
    cmd_validate,
)
from src.liveapi.metadata_manager import ProjectStatus


class TestHandleNoCommand:
    """Test the handle_no_command function."""

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_uninitialized_project_choice_1(
        self, mock_print, mock_input, mock_metadata
    ):
        """Test interactive mode choice 1: initialize and generate."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        mock_input.side_effect = ["1", "test-project", "y"]

        with patch("src.liveapi.cli.commands.project.cmd_init") as mock_init, patch(
            "src.liveapi.cli.commands.generate.cmd_generate"
        ) as mock_generate:

            handle_no_command()

            # Verify init was called
            mock_init.assert_called_once()
            args = mock_init.call_args[0][0]
            assert args.name == "test-project"

            # Verify generate was called
            mock_generate.assert_called_once()

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_uninitialized_project_choice_2(
        self, mock_print, mock_input, mock_metadata
    ):
        """Test interactive mode choice 2: just initialize."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        mock_input.return_value = "2"

        with patch("src.liveapi.cli.commands.project.cmd_init") as mock_init:
            handle_no_command()

            mock_init.assert_called_once()
            args = mock_init.call_args[0][0]
            assert args.name is None

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_uninitialized_project_choice_3(
        self, mock_print, mock_input, mock_metadata
    ):
        """Test interactive mode choice 3: show help."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        mock_input.return_value = "3"

        handle_no_command()

        # Should print help message
        mock_print.assert_any_call("\nRun 'liveapi --help' for usage information.")

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    def test_initialized_project_no_changes(
        self, mock_print, mock_change_detector, mock_metadata
    ):
        """Test initialized project with no changes."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.INITIALIZED
        mock_metadata.return_value = mock_manager

        mock_detector = Mock()
        mock_detector.detect_all_changes.return_value = {}
        mock_change_detector.return_value = mock_detector

        handle_no_command()

        mock_print.assert_any_call("✅ All specifications are synchronized")

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    def test_initialized_project_with_changes(
        self, mock_print, mock_change_detector, mock_metadata
    ):
        """Test initialized project with pending changes."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.INITIALIZED
        mock_metadata.return_value = mock_manager

        mock_detector = Mock()
        mock_detector.detect_all_changes.return_value = {
            "spec1.yaml": Mock(),
            "spec2.yaml": Mock(),
        }
        mock_change_detector.return_value = mock_detector

        handle_no_command()

        mock_print.assert_any_call("📋 2 specification(s) have pending changes")


class TestCmdInit:
    """Test the cmd_init function."""

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_successful_init_with_specs(
        self, mock_print, mock_input, mock_change_detector, mock_metadata
    ):
        """Test successful initialization with existing specs."""
        # Setup mocks
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        mock_detector = Mock()
        mock_detector.find_api_specs.return_value = [
            Path("api.yaml"),
            Path("users.yaml"),
        ]
        mock_change_detector.return_value = mock_detector

        mock_input.return_value = "api.example.com"

        args = Mock()
        args.name = "test-project"

        cmd_init(args)

        # Verify initialization was called
        mock_manager.initialize_project.assert_called_once_with(
            "test-project", "api.example.com"
        )

        # Verify specs were tracked
        assert mock_detector.update_spec_tracking.call_count == 2
        mock_manager.update_last_sync.assert_called_once()

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_init_no_specs_found(
        self, mock_print, mock_input, mock_change_detector, mock_metadata
    ):
        """Test initialization when no specs are found."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        mock_detector = Mock()
        mock_detector.find_api_specs.return_value = []
        mock_change_detector.return_value = mock_detector

        mock_input.return_value = ""

        args = Mock()
        args.name = None

        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value.name = "my-project"
            cmd_init(args)

        mock_manager.initialize_project.assert_called_once_with("my-project", None)
        mock_print.assert_any_call("📋 No OpenAPI specifications found")

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("builtins.print")
    def test_init_already_initialized(self, mock_print, mock_metadata):
        """Test initialization when project is already initialized."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.INITIALIZED
        mock_metadata.return_value = mock_manager

        args = Mock()
        args.name = "test"

        cmd_init(args)

        mock_print.assert_called_with("⚠️  Project is already initialized")
        mock_manager.initialize_project.assert_not_called()

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_init_keyboard_interrupt(
        self, mock_print, mock_input, mock_change_detector, mock_metadata
    ):
        """Test handling keyboard interrupt during URL input."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        mock_detector = Mock()
        mock_detector.find_api_specs.return_value = []
        mock_change_detector.return_value = mock_detector

        mock_input.side_effect = KeyboardInterrupt()

        args = Mock()
        args.name = "test-project"

        cmd_init(args)

        mock_manager.initialize_project.assert_called_once_with("test-project", None)
        mock_print.assert_any_call("\n⚠️  Skipping API base URL setup")

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_init_url_with_protocol(
        self, mock_print, mock_input, mock_change_detector, mock_metadata
    ):
        """Test URL input with protocol gets cleaned."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        mock_detector = Mock()
        mock_detector.find_api_specs.return_value = []
        mock_change_detector.return_value = mock_detector

        mock_input.return_value = "https://api.example.com"

        args = Mock()
        args.name = "test-project"

        cmd_init(args)

        mock_manager.initialize_project.assert_called_once_with(
            "test-project", "api.example.com"
        )
        mock_print.assert_any_call("⚠️  Using domain: api.example.com")


class TestCmdStatus:
    """Test the cmd_status function."""

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("builtins.print")
    def test_status_uninitialized(self, mock_print, mock_metadata):
        """Test status command on uninitialized project."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        args = Mock()
        args.check = False

        cmd_status(args)

        mock_print.assert_called_with(
            "❌ Project not initialized. Run 'liveapi init' first."
        )

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("sys.exit")
    def test_status_uninitialized_with_check(self, mock_exit, mock_metadata):
        """Test status command with --check flag on uninitialized project."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.UNINITIALIZED
        mock_metadata.return_value = mock_manager

        args = Mock()
        args.check = True

        cmd_status(args)

        mock_exit.assert_called_with(1)

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    def test_status_no_changes(self, mock_print, mock_change_detector, mock_metadata):
        """Test status when no changes detected."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.INITIALIZED
        mock_config = Mock()
        mock_config.project_name = "test-project"
        mock_config.created_at = "2024-01-01"
        mock_config.last_sync = "2024-01-02"
        mock_config.api_base_url = "api.test.com"
        mock_manager.load_config.return_value = mock_config
        mock_metadata.return_value = mock_manager

        mock_detector = Mock()
        mock_detector.detect_all_changes.return_value = {}
        mock_change_detector.return_value = mock_detector

        args = Mock()
        args.check = False

        cmd_status(args)

        mock_print.assert_any_call("✅ All specifications are up to date")

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    def test_status_with_breaking_changes(
        self, mock_print, mock_change_detector, mock_metadata
    ):
        """Test status with breaking changes."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.INITIALIZED
        mock_config = Mock()
        mock_config.project_name = "test-project"
        mock_config.created_at = "2024-01-01"
        mock_config.last_sync = None
        mock_config.api_base_url = None
        mock_manager.load_config.return_value = mock_config
        mock_metadata.return_value = mock_manager

        # Mock breaking changes
        mock_change = Mock()
        mock_change.is_breaking = True
        mock_change.description = "Removed required field"

        mock_analysis = Mock()
        mock_analysis.is_breaking = True
        mock_analysis.summary = "Breaking changes detected"
        mock_analysis.changes = [mock_change]

        mock_detector = Mock()
        mock_detector.detect_all_changes.return_value = {"api.yaml": mock_analysis}
        mock_change_detector.return_value = mock_detector

        args = Mock()
        args.check = False

        cmd_status(args)

        mock_print.assert_any_call("⚠️  1 of 1 specifications have breaking changes")

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("sys.exit")
    def test_status_with_check_flag_breaking(
        self, mock_exit, mock_change_detector, mock_metadata
    ):
        """Test status with --check flag and breaking changes."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.INITIALIZED
        mock_config = Mock()
        mock_config.project_name = "test"
        mock_config.created_at = "2024-01-01"
        mock_config.last_sync = None
        mock_config.api_base_url = None
        mock_manager.load_config.return_value = mock_config
        mock_metadata.return_value = mock_manager

        mock_analysis = Mock()
        mock_analysis.is_breaking = True
        mock_analysis.summary = "Breaking"
        mock_analysis.changes = []

        mock_detector = Mock()
        mock_detector.detect_all_changes.return_value = {"api.yaml": mock_analysis}
        mock_change_detector.return_value = mock_detector

        args = Mock()
        args.check = True

        cmd_status(args)

        mock_exit.assert_called_with(1)

    @patch("src.liveapi.cli.commands.project.MetadataManager")
    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("sys.exit")
    def test_status_with_check_flag_non_breaking(
        self, mock_exit, mock_change_detector, mock_metadata
    ):
        """Test status with --check flag and non-breaking changes."""
        mock_manager = Mock()
        mock_manager.get_project_status.return_value = ProjectStatus.INITIALIZED
        mock_config = Mock()
        mock_config.project_name = "test"
        mock_config.created_at = "2024-01-01"
        mock_config.last_sync = None
        mock_config.api_base_url = None
        mock_manager.load_config.return_value = mock_config
        mock_metadata.return_value = mock_manager

        mock_analysis = Mock()
        mock_analysis.is_breaking = False
        mock_analysis.summary = "Non-breaking"
        mock_analysis.changes = []

        mock_detector = Mock()
        mock_detector.detect_all_changes.return_value = {"api.yaml": mock_analysis}
        mock_change_detector.return_value = mock_detector

        args = Mock()
        args.check = True

        cmd_status(args)

        mock_exit.assert_called_with(0)


class TestCmdValidate:
    """Test the cmd_validate function."""

    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    def test_validate_no_specs(self, mock_print, mock_change_detector):
        """Test validate when no specs found."""
        mock_detector = Mock()
        mock_detector.find_api_specs.return_value = []
        mock_change_detector.return_value = mock_detector

        args = Mock()

        cmd_validate(args)

        mock_print.assert_called_with("📋 No OpenAPI specifications found")

    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    def test_validate_valid_specs(self, mock_print, mock_change_detector):
        """Test validate with valid specifications."""
        mock_detector = Mock()
        mock_spec1 = Mock()
        mock_spec1.name = "api.yaml"
        mock_spec2 = Mock()
        mock_spec2.name = "users.yaml"
        mock_detector.find_api_specs.return_value = [mock_spec1, mock_spec2]

        # Mock valid spec data
        valid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/test": {"get": {"responses": {"200": {"description": "OK"}}}}},
        }
        mock_detector._load_spec.return_value = valid_spec
        mock_change_detector.return_value = mock_detector

        args = Mock()

        cmd_validate(args)

        mock_print.assert_any_call("   ✅ api.yaml: Valid")
        mock_print.assert_any_call("   ✅ users.yaml: Valid")
        mock_print.assert_any_call("✅ All 2 specifications are valid")

    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    @patch("sys.exit")
    def test_validate_invalid_specs(self, mock_exit, mock_print, mock_change_detector):
        """Test validate with invalid specifications."""
        mock_detector = Mock()
        mock_spec = Mock()
        mock_spec.name = "invalid.yaml"
        mock_detector.find_api_specs.return_value = [mock_spec]

        # Mock invalid spec (missing required fields)
        mock_detector._load_spec.return_value = {"openapi": "3.0.0"}
        mock_change_detector.return_value = mock_detector

        args = Mock()

        cmd_validate(args)

        mock_print.assert_any_call("   ❌ invalid.yaml: Missing 'info' section")
        mock_print.assert_any_call("❌ 1 specification(s) have errors")
        mock_exit.assert_called_with(1)

    @patch("src.liveapi.cli.commands.project.ChangeDetector")
    @patch("builtins.print")
    def test_validate_mixed_specs(self, mock_print, mock_change_detector):
        """Test validate with mix of valid and invalid specs."""
        mock_detector = Mock()
        mock_spec1 = Mock()
        mock_spec1.name = "valid.yaml"
        mock_spec2 = Mock()
        mock_spec2.name = "invalid.yaml"
        mock_detector.find_api_specs.return_value = [mock_spec1, mock_spec2]

        def mock_load_spec(spec_path):
            if spec_path.name == "valid.yaml":
                return {
                    "openapi": "3.0.0",
                    "info": {"title": "Test", "version": "1.0.0"},
                    "paths": {},
                }
            else:
                return {"openapi": "3.0.0"}  # Missing info and paths

        mock_detector._load_spec.side_effect = mock_load_spec
        mock_change_detector.return_value = mock_detector

        args = Mock()

        with patch("sys.exit") as mock_exit:
            cmd_validate(args)
            mock_exit.assert_called_with(1)

        mock_print.assert_any_call("   ✅ valid.yaml: Valid")
        mock_print.assert_any_call("   ❌ invalid.yaml: Missing 'info' section")

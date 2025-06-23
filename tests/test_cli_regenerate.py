"""Tests for CLI regenerate command."""

import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from liveapi.cli import cmd_regenerate


class TestCLIRegenerate:
    """Test the CLI regenerate command."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.prompts_dir = Path(self.temp_dir) / ".liveapi" / "prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Change to temp directory for tests
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_regenerate_missing_prompt_file(self, capsys):
        """Test regenerate command with missing prompt file."""

        class Args:
            def __init__(self):
                self.prompt_file = "nonexistent.json"
                self.output = None
                self.format = "yaml"

        args = Args()
        # Test with missing file
        with pytest.raises(SystemExit) as excinfo:
            cmd_regenerate(args)

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Prompt file not found" in captured.out

    def test_regenerate_lists_available_prompts(self, capsys):
        """Test that missing prompt file shows available prompts."""
        # Create some test prompt files
        prompt1 = self.prompts_dir / "api1_prompt.json"
        prompt2 = self.prompts_dir / "api2_prompt.json"

        for prompt_file in [prompt1, prompt2]:
            with open(prompt_file, "w") as f:
                json.dump({"api_info": {"name": "test"}}, f)

        class Args:
            def __init__(self):
                self.prompt_file = "nonexistent.json"
                self.output = None
                self.format = "yaml"

        args = Args()
        with pytest.raises(SystemExit):
            cmd_regenerate(args)

        captured = capsys.readouterr()
        assert "Available prompt files:" in captured.out
        assert "api1_prompt.json" in captured.out
        assert "api2_prompt.json" in captured.out

    # No longer need to patch environment variables for API key
    @patch("liveapi.cli.commands.generate.SpecGenerator")
    @patch("liveapi.cli.commands.generate.MetadataManager")
    @patch("liveapi.cli.commands.generate.ChangeDetector")
    def test_regenerate_success(
        self, mock_change_detector, mock_metadata_manager, mock_spec_generator, capsys
    ):
        """Test successful regeneration from prompt file."""
        # Create a valid prompt file
        prompt_data = {
            "api_info": {
                "name": "Test API",
                "description": "Test description",
                "endpoint_descriptions": "/test - test endpoint",
            },
            "metadata": {"created_at": "2023-01-01T00:00:00", "model": "openai/gpt-4o"},
        }

        prompt_file = self.prompts_dir / "test_prompt.json"
        with open(prompt_file, "w") as f:
            json.dump(prompt_data, f)

        # Mock the generator
        mock_generator_instance = MagicMock()
        mock_spec_generator.return_value = mock_generator_instance

        # Mock the generated spec
        mock_spec = {
            "info": {"title": "Test API", "version": "1.0.0"},
            "openapi": "3.0.3",
        }
        mock_generator_instance.interactive_generate.return_value = mock_spec
        mock_generator_instance.save_spec.return_value = "specifications/test_api.yaml"

        # Mock project status
        mock_metadata_instance = MagicMock()
        mock_metadata_manager.return_value = mock_metadata_instance
        mock_metadata_instance.get_project_status.return_value.UNINITIALIZED = False

        # Mock change detector
        mock_change_detector_instance = MagicMock()
        mock_change_detector.return_value = mock_change_detector_instance

        class Args:
            def __init__(self):
                self.prompt_file = str(prompt_file)
                self.output = None
                self.format = "yaml"

        args = Args()

        cmd_regenerate(args)

        # Verify the generator was called correctly
        mock_spec_generator.assert_called_once_with()
        mock_generator_instance.interactive_generate.assert_called_once_with(
            prompt_file=str(prompt_file)
        )
        mock_generator_instance.save_spec.assert_called_once()

        captured = capsys.readouterr()
        assert "Specification regenerated and saved" in captured.out
        assert "specifications/test_api.yaml" in captured.out

    @patch("liveapi.cli.commands.generate.SpecGenerator")
    def test_regenerate_with_custom_output(self, mock_spec_generator):
        """Test regeneration with custom output path."""
        # Create a valid prompt file
        prompt_data = {
            "api_info": {
                "name": "Custom API",
                "description": "Custom description",
                "endpoint_descriptions": "/custom - custom endpoint",
            }
        }

        prompt_file = self.prompts_dir / "custom_prompt.json"
        with open(prompt_file, "w") as f:
            json.dump(prompt_data, f)

        # Mock the generator
        mock_generator_instance = MagicMock()
        mock_spec_generator.return_value = mock_generator_instance
        mock_generator_instance.interactive_generate.return_value = {
            "info": {"title": "Custom API"}
        }
        mock_generator_instance.save_spec.return_value = "custom_output.json"

        class Args:
            def __init__(self):
                self.prompt_file = str(prompt_file)
                self.output = "custom_output.json"
                self.format = "json"

        args = Args()
        cmd_regenerate(args)

        # Verify the generator was called correctly
        mock_spec_generator.assert_called_once_with()

        # Verify save_spec was called with custom output
        mock_generator_instance.save_spec.assert_called_once()
        call_args = mock_generator_instance.save_spec.call_args
        assert call_args[0][1] == "custom_output.json"  # output path
        assert call_args[0][2] == "json"  # format

    @patch("liveapi.cli.commands.generate.SpecGenerator")
    def test_regenerate_generation_failure(self, mock_spec_generator, capsys):
        """Test regenerate command when generation fails."""
        # Create a valid prompt file
        prompt_file = self.prompts_dir / "test_prompt.json"
        with open(prompt_file, "w") as f:
            json.dump({"api_info": {"name": "test"}}, f)

        # Mock generator to raise an exception
        mock_generator_instance = MagicMock()
        mock_spec_generator.return_value = mock_generator_instance
        mock_generator_instance.interactive_generate.side_effect = Exception(
            "Generation failed"
        )

        class Args:
            def __init__(self):
                self.prompt_file = str(prompt_file)
                self.output = None
                self.format = "yaml"

        args = Args()

        with pytest.raises(SystemExit) as excinfo:
            cmd_regenerate(args)

        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Regeneration failed: Generation failed" in captured.out

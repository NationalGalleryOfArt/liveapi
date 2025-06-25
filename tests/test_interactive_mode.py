"""Test interactive mode end-to-end functionality."""

import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from liveapi.generator.interactive import InteractiveGenerator
from liveapi.generator.generator import SpecGenerator


class TestInteractiveMode:
    """Test the simplified interactive mode workflow."""

    def test_simplified_interactive_workflow(self):
        """Test the complete simplified interactive workflow."""
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mock .liveapi directory
            liveapi_dir = temp_path / ".liveapi"
            liveapi_dir.mkdir()
            prompts_dir = liveapi_dir / "prompts"
            prompts_dir.mkdir()

            # Mock user inputs for the simplified workflow
            user_inputs = [
                "products",  # object name (now first)
                "Product inventory items",  # object description
                "Product Catalog API",  # API name (with default shown)
                "API for managing product catalog",  # API description (with default shown)
                "1",  # backend choice (DefaultResource)
                # JSON attributes (with double newlines to end input)
                '{\n  "name": "string",\n  "price": "number",\n  "category": "string",\n  "inStock": "boolean"\n}',
                "",  # first empty line
                "",  # second empty line to end JSON input
                # JSON array examples (new format)
                '[\n  {\n    "name": "Gaming Laptop",\n    "price": 1299.99,\n    "category": "Electronics",\n    "inStock": true\n  },\n  {\n    "name": "Office Chair",\n    "price": 249.99,\n    "category": "Furniture",\n    "inStock": false\n  }\n]',
                "",  # first empty line
                "",  # second empty line to end examples
            ]

            with patch("builtins.input", side_effect=user_inputs):
                # Create spec generator and interactive generator
                spec_generator = SpecGenerator()
                interactive_gen = InteractiveGenerator(spec_generator)

                # Collect API info using the simplified workflow
                api_info = interactive_gen.collect_api_info()

                # Verify the collected information
                expected_api_info = {
                    "name": "Product Catalog API",
                    "description": "API for managing product catalog",
                    "project_name": "products",  # Auto-inferred from resource name
                    "base_url": "https://api.example.com",  # Default value
                    "is_crud": True,
                    "resource_name": "products",
                    "resource_description": "Product inventory items",
                    "resource_schema": {
                        "name": "string",
                        "price": "number",
                        "category": "string",
                        "inStock": "boolean",
                    },
                    "examples": [
                        {
                            "name": "Gaming Laptop",
                            "price": 1299.99,
                            "category": "Electronics",
                            "inStock": True,
                        },
                        {
                            "name": "Office Chair",
                            "price": 249.99,
                            "category": "Furniture",
                            "inStock": False,
                        },
                    ],
                    "backend_type": "default",
                }

                assert api_info == expected_api_info

    def test_api_info_validation(self):
        """Test that API info contains all required fields."""
        spec_generator = SpecGenerator()
        interactive_gen = InteractiveGenerator(spec_generator)

        # Mock minimal inputs (new workflow order)
        user_inputs = [
            "items",  # object name (now first)
            "Test items",  # object description
            "Test API",  # API name (with default shown)
            "Test description",  # API description (with default shown)
            "1",  # backend choice (DefaultResource)
            '{"name": "string"}',  # JSON attributes
            "",  # first empty line
            "",  # second empty line
            '[{"name": "Item 1"}, {"name": "Item 2"}]',  # JSON array examples
            "",  # first empty line
            "",  # second empty line
        ]

        with patch("builtins.input", side_effect=user_inputs):
            api_info = interactive_gen.collect_api_info()

            # Check all required fields are present
            required_fields = [
                "name",
                "description",
                "project_name",
                "base_url",
                "is_crud",
                "resource_name",
                "resource_description",
                "resource_schema",
                "examples",
                "backend_type",
            ]

            for field in required_fields:
                assert field in api_info, f"Missing required field: {field}"

            # Check CRUD is always True in simplified mode
            assert api_info["is_crud"] is True

            # Check examples are properly parsed
            assert len(api_info["examples"]) == 2
            assert api_info["examples"][0]["name"] == "Item 1"
            assert api_info["examples"][1]["name"] == "Item 2"

    def test_default_values(self):
        """Test that default values are applied when user provides empty input."""
        spec_generator = SpecGenerator()
        interactive_gen = InteractiveGenerator(spec_generator)

        # Mock empty inputs to test defaults (new workflow order)
        user_inputs = [
            "",  # Empty object name -> "items"
            "",  # Empty object description -> "A items resource"
            "",  # Empty API name -> "Items API" (auto-inferred)
            "",  # Empty API description -> "A items resource" (auto-inferred)
            "",  # Empty backend choice -> default
            "",  # Empty JSON -> default schema
            "",  # first empty line
            "",  # second empty line (invalid JSON)
            "",  # Empty examples (JSON array)
            "",  # first empty line
            "",  # second empty line
        ]

        with patch("builtins.input", side_effect=user_inputs):
            api_info = interactive_gen.collect_api_info()

            # Check defaults are applied (new smart defaults)
            assert api_info["name"] == "Items API"  # Auto-inferred from resource name
            assert (
                api_info["description"] == "A items resource"
            )  # Auto-inferred from resource description
            assert (
                api_info["project_name"] == "items"
            )  # Auto-inferred from resource name
            assert api_info["base_url"] == "https://api.example.com"
            assert api_info["resource_name"] == "items"
            assert api_info["resource_description"] == "A items resource"
            assert api_info["resource_schema"] == {
                "name": "string",
                "description": "string",
            }
            assert len(api_info["examples"]) == 2  # Default examples created

    def test_json_parsing_error_handling(self):
        """Test handling of invalid JSON input."""
        spec_generator = SpecGenerator()
        interactive_gen = InteractiveGenerator(spec_generator)

        # Mock inputs with invalid JSON (new workflow order)
        user_inputs = [
            "items",  # object name (now first)
            "Test items",  # object description
            "Test API",  # API name (with default shown)
            "Test description",  # API description (with default shown)
            "1",  # backend choice (DefaultResource)
            "invalid json {",  # Invalid JSON attributes
            "",  # first empty line
            "",  # second empty line
            '[{"valid": "json"}]',  # Valid JSON array example
            "",  # first empty line
            "",  # second empty line
        ]

        with patch("builtins.input", side_effect=user_inputs):
            with patch("builtins.print"):  # Suppress warning prints
                api_info = interactive_gen.collect_api_info()

                # Should fall back to default schema for invalid JSON
                assert api_info["resource_schema"] == {
                    "name": "string",
                    "description": "string",
                }

                # Should have one valid example from the JSON array
                assert len(api_info["examples"]) == 1
                assert api_info["examples"][0] == {"valid": "json"}

    def test_save_and_load_prompt(self):
        """Test saving and loading prompt data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create mock .liveapi directory
            liveapi_dir = temp_path / ".liveapi"
            liveapi_dir.mkdir()

            spec_generator = SpecGenerator()
            interactive_gen = InteractiveGenerator(spec_generator)

            # Mock the metadata manager to use our temp directory
            with patch("liveapi.metadata_manager.MetadataManager") as mock_metadata:
                mock_metadata.return_value.project_root = temp_path

                # Test data
                api_info = {
                    "name": "Test API",
                    "description": "Test description",
                    "project_name": "test_api",
                    "base_url": "https://api.test.com",
                    "is_crud": True,
                    "resource_name": "items",
                    "resource_description": "Test items",
                    "resource_schema": {"name": "string"},
                    "examples": [{"name": "Item 1"}],
                    "backend_type": "default",
                }

                spec = {"info": {"title": "Test API", "version": "1.0.0"}}
                llm_json = {"endpoints": [], "objects": []}

                # Save prompt and schema
                interactive_gen.save_prompt_and_json(api_info, spec, llm_json)

                # Check files were created
                prompts_dir = temp_path / ".liveapi" / "prompts"
                prompt_file = prompts_dir / "test_api_prompt.json"
                schema_file = prompts_dir / "test_api_schema.json"

                assert prompt_file.exists()
                assert schema_file.exists()

                # Load and verify prompt data
                loaded_api_info = interactive_gen.load_prompt(str(prompt_file))
                assert loaded_api_info == api_info

                # Verify schema file content
                with open(schema_file) as f:
                    loaded_schema = json.load(f)
                assert loaded_schema == llm_json

    def test_existing_info_handling(self):
        """Test handling of existing API info for regeneration."""
        spec_generator = SpecGenerator()
        interactive_gen = InteractiveGenerator(spec_generator)

        existing_info = {
            "name": "Existing API",
            "description": "Existing description",
            "project_name": "existing_api",
            "base_url": "https://api.existing.com",
            "resource_name": "items",
            "resource_description": "Existing items",
            "resource_schema": {"name": "string", "id": "integer"},
            "examples": [{"name": "Existing Item"}],
            "backend_type": "default",
        }

        # User just presses enter to accept existing values
        user_inputs = [""] * 20  # Enough empty inputs

        with patch("builtins.input", side_effect=user_inputs):
            api_info = interactive_gen.collect_api_info(existing_info)

            # Should keep existing values when user provides empty input
            assert api_info["name"] == "Existing API"
            assert api_info["description"] == "Existing description"
            assert api_info["project_name"] == "existing_api"
            assert api_info["base_url"] == "https://api.existing.com"

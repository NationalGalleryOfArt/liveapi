"""Tests for spec generator module."""

import json
import os
from pathlib import Path
from unittest.mock import patch
import tempfile
import datetime

from liveapi.spec_generator import SpecGenerator


class TestSpecGenerator:
    """Test OpenAPI spec generation."""

    def test_init(self):
        """Test initialization."""
        generator = SpecGenerator()
        # Just verify it initializes without error
        assert generator is not None
        
    def test_status_codes_by_method(self):
        """Test that appropriate status codes are used based on HTTP method."""
        generator = SpecGenerator()
        
        api_info = {
            "name": "Status Code Test API",
            "description": "API for testing status codes",
            "is_crud": True,
            "resource_name": "items",
            "resource_schema": {"name": "string"}
        }
        
        result = generator.generate_spec(api_info)
        
        # Test POST operation uses 201 Created
        assert "201" in result["paths"]["/items"]["post"]["responses"]
        assert "200" not in result["paths"]["/items"]["post"]["responses"]
        assert result["paths"]["/items"]["post"]["responses"]["201"]["description"] == "Created"
        
        # Test DELETE operation uses 204 No Content
        assert "204" in result["paths"]["/items/{id}"]["delete"]["responses"]
        assert "200" not in result["paths"]["/items/{id}"]["delete"]["responses"]
        assert result["paths"]["/items/{id}"]["delete"]["responses"]["204"]["description"] == "No Content"
        
        # Test GET operation uses 200 OK
        assert "200" in result["paths"]["/items"]["get"]["responses"]
        assert result["paths"]["/items"]["get"]["responses"]["200"]["description"] == "Success"
        
        # Test PUT operation uses 200 OK
        assert "200" in result["paths"]["/items/{id}"]["put"]["responses"]
        assert result["paths"]["/items/{id}"]["put"]["responses"]["200"]["description"] == "Success"

    def test_error_response_examples(self):
        """Test that error responses have correct examples."""
        generator = SpecGenerator()
        
        api_info = {
            "name": "Error Test API",
            "description": "API for testing error responses",
            "is_crud": True,
            "resource_name": "items",
            "resource_schema": {"name": "string"}
        }
        
        result = generator.generate_spec(api_info)
        
        # Get a sample endpoint to test error responses
        endpoint_responses = result["paths"]["/items"]["get"]["responses"]
        
        # Test 400 Bad Request example
        assert "example" in endpoint_responses["400"]["content"]["application/problem+json"]
        bad_request_example = endpoint_responses["400"]["content"]["application/problem+json"]["example"]
        assert bad_request_example["status"] == 400
        assert bad_request_example["title"] == "Bad Request"
        
        # Test 401 Unauthorized example
        assert "example" in endpoint_responses["401"]["content"]["application/problem+json"]
        unauthorized_example = endpoint_responses["401"]["content"]["application/problem+json"]["example"]
        assert unauthorized_example["status"] == 401
        assert unauthorized_example["title"] == "Unauthorized"
        
        # Test 500 Internal Server Error example
        assert "example" in endpoint_responses["500"]["content"]["application/problem+json"]
        server_error_example = endpoint_responses["500"]["content"]["application/problem+json"]["example"]
        assert server_error_example["status"] == 500
        assert server_error_example["title"] == "Internal Server Error"
        
        # Test 503 Service Unavailable example
        assert "example" in endpoint_responses["503"]["content"]["application/problem+json"]
        unavailable_example = endpoint_responses["503"]["content"]["application/problem+json"]["example"]
        assert unavailable_example["status"] == 503
        assert unavailable_example["title"] == "Service Unavailable"

    def test_build_prompt(self):
        """Test prompt building."""
        # Create generator for testing
        SpecGenerator()

        # Create API info for testing (not used in this simple test)
        {
            "name": "Art Gallery API",
            "description": "Art locations for an art gallery",
            "endpoint_descriptions": """/locations - returns all locations - locations contain:
[locationID] [int] NOT NULL,
[site] [nvarchar](64) NULL,
[room] [nvarchar](64) NULL,
[active] [int] NOT NULL,
[description] [nvarchar](256) NULL,
[unitPosition] [nvarchar](64) NULL""",
        }

        # Method was removed - this test is no longer applicable
        pass

    def test_generate_spec_crud(self):
        """Test CRUD spec generation."""
        generator = SpecGenerator()

        api_info = {
            "name": "Test API",
            "description": "Test API description",
            "is_crud": True,
            "resource_name": "users",
            "resource_schema": {"name": "string", "email": "string"},
        }

        result = generator.generate_spec(api_info)

        assert result["openapi"] == "3.0.3"
        assert result["info"]["title"] == "Test API"
        assert "/users" in result["paths"]
        assert "get" in result["paths"]["/users"]
        assert "/users/{id}" in result["paths"]
        assert "User" in result["components"]["schemas"]
        assert "name" in result["components"]["schemas"]["User"]["properties"]
        assert "email" in result["components"]["schemas"]["User"]["properties"]

    def test_save_spec_yaml(self):
        """Test saving spec as YAML."""
        generator = SpecGenerator()

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_api")
            saved_path = generator.save_spec(spec, output_path, "yaml")

            assert saved_path.endswith(".yaml")
            assert os.path.exists(saved_path)

            # Verify content
            with open(saved_path) as f:
                content = f.read()
                assert "openapi: '3.0.3'" in content or "openapi: 3.0.3" in content
                assert "Test API" in content

    def test_save_spec_json(self):
        """Test saving spec as JSON."""
        generator = SpecGenerator()

        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_api")
            saved_path = generator.save_spec(spec, output_path, "json")

            assert saved_path.endswith(".json")
            assert os.path.exists(saved_path)

            # Verify content
            with open(saved_path) as f:
                loaded = json.load(f)
                assert loaded["openapi"] == "3.0.3"
                assert loaded["info"]["title"] == "Test API"

    @patch("builtins.input")
    def test_interactive_generate(self, mock_input):
        """Test interactive generation flow."""
        generator = SpecGenerator()

        # Mock user inputs for simplified workflow (new order)
        mock_input.side_effect = [
            "locations",  # object name (now first)
            "Gallery location records",  # object description
            "Art Gallery API",  # API name (with default shown)
            "Art locations for an art gallery",  # API description (with default shown)
            "1",  # backend choice (DefaultResourceService)
            '{"locationID": "integer", "site": "string", "room": "string"}',  # JSON schema (one line)
            "",  # Empty line 1
            "",  # Empty line 2 (end JSON input)
            # Example 1
            '{"locationID": 1, "site": "Main Gallery", "room": "101"}',  # Example 1 (one line)
            "",  # Empty line 1
            "",  # Empty line 2 (end example 1)
            # Example 2
            '{"locationID": 2, "site": "Annex", "room": "202"}',  # Example 2 (one line)
            "",  # Empty line 1
            "",  # Empty line 2 (end example 2)
        ]

        result = generator.interactive_generate()

        assert result["info"]["title"] == "Art Gallery API"
        assert result["openapi"] == "3.0.3"
        assert result["info"]["version"] == "1.0.0"
        assert "/locations" in result["paths"]
        assert "Location" in result["components"]["schemas"]
        assert "locationID" in result["components"]["schemas"]["Location"]["properties"]
        assert "site" in result["components"]["schemas"]["Location"]["properties"]
        assert "room" in result["components"]["schemas"]["Location"]["properties"]


# API Key Management tests removed as they are no longer needed


class TestPromptPersistence:
    """Test prompt saving and loading functionality."""

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

    @patch("builtins.input")
    def test_save_prompt_during_generation(self, mock_input):
        """Test that prompts are automatically saved during generation."""
        generator = SpecGenerator()

        # Mock user inputs for simplified workflow (new order)
        mock_input.side_effect = [
            "users",  # object name (now first)
            "User account records",  # object description
            "User Management API",  # API name (with default shown)
            "Manage user accounts and profiles",  # API description (with default shown)
            "1",  # backend choice (DefaultResourceService)
            '{"userID": "integer", "email": "string"}',  # JSON schema (one line)
            "",  # Empty line 1
            "",  # Empty line 2 (end JSON input)
            # Example 1
            '{"userID": 1, "email": "user1@test.com"}',  # Example 1 (one line)
            "",  # Empty line 1
            "",  # Empty line 2
            # Example 2
            '{"userID": 2, "email": "user2@test.com"}',  # Example 2 (one line)
            "",  # Empty line 1
            "",  # Empty line 2
        ]

        # Generate spec
        generator.interactive_generate()

        # Check that prompt file was created (using auto-inferred project name)
        prompt_file = (
            self.prompts_dir / "users_prompt.json"
        )  # Auto-inferred from resource name
        assert prompt_file.exists()

        # Verify prompt content
        with open(prompt_file) as f:
            prompt_data = json.load(f)

        assert "api_info" in prompt_data
        assert "metadata" in prompt_data

        api_info = prompt_data["api_info"]
        assert api_info["name"] == "User Management API"
        assert api_info["description"] == "Manage user accounts and profiles"
        assert api_info["project_name"] == "users"  # Auto-inferred from resource name
        assert api_info["is_crud"] is True
        assert api_info["resource_name"] == "users"
        assert "userID" in api_info["resource_schema"]
        assert "email" in api_info["resource_schema"]

        metadata = prompt_data["metadata"]
        assert "created_at" in metadata
        assert metadata["model"] == "structured-generator"
        assert metadata["generated_spec_title"] == "User Management API"

    def test_load_prompt_from_file(self):
        """Test loading saved prompt data."""
        generator = SpecGenerator()

        # Create a test prompt file
        prompt_data = {
            "api_info": {
                "name": "Test API",
                "description": "Test description",
                "endpoint_descriptions": "/test - test endpoint",
            },
            "metadata": {
                "created_at": datetime.datetime.now().isoformat(),
                "model": "openai/gpt-4o",
                "generated_spec_title": "Test API",
                "generated_spec_version": "1.0.0",
            },
        }

        prompt_file = self.prompts_dir / "test_prompt.json"
        with open(prompt_file, "w") as f:
            json.dump(prompt_data, f)

        # Load the prompt
        loaded_api_info = generator.load_prompt(str(prompt_file))

        assert loaded_api_info["name"] == "Test API"
        assert loaded_api_info["description"] == "Test description"
        assert loaded_api_info["endpoint_descriptions"] == "/test - test endpoint"

    @patch("builtins.input")
    def test_interactive_generate_with_existing_prompt(self, mock_input):
        """Test interactive generation using an existing prompt."""
        generator = SpecGenerator()

        # Create an existing prompt file
        prompt_data = {
            "api_info": {
                "name": "Existing API",
                "description": "An existing API",
                "endpoint_descriptions": "/existing - existing endpoint",
                "is_crud": True,
                "resource_name": "existing",
                "resource_schema": {"id": "integer", "name": "string"},
            },
            "metadata": {
                "created_at": datetime.datetime.now().isoformat(),
                "model": "structured-generator",
            },
        }

        prompt_file = self.prompts_dir / "existing_prompt.json"
        with open(prompt_file, "w") as f:
            json.dump(prompt_data, f)

        # Mock user choosing to use existing prompt
        mock_input.side_effect = ["y"]  # Use saved prompt

        # Create a schema file to go with the prompt
        schema_data = {
            "endpoints": [
                {
                    "path": "/existing",
                    "method": "GET",
                    "description": "Existing endpoint",
                    "returns": "object",
                }
            ],
            "objects": [
                {
                    "name": "ExistingObject",
                    "fields": {"id": "integer"},
                }
            ],
        }

        schema_file = self.prompts_dir / "existing_schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        # Generate using existing prompt
        spec = generator.interactive_generate(prompt_file=str(prompt_file))

        assert spec["info"]["title"] == "Existing API"

        # Verify the spec was generated correctly
        assert spec["info"]["title"] == "Existing API"
        assert "/existing" in spec["paths"]
        assert "Existing" in spec["components"]["schemas"]

    @patch("builtins.input")
    def test_interactive_generate_edit_existing_prompt(self, mock_input):
        """Test interactive generation with editing an existing prompt."""
        generator = SpecGenerator()

        # Create an existing prompt file (new CRUD format)
        prompt_data = {
            "api_info": {
                "name": "Old API",
                "description": "Old description",
                "project_name": "old_api",
                "base_url": "https://api.old.com",
                "is_crud": True,
                "resource_name": "items",
                "resource_description": "Old items",
                "resource_schema": {"name": "string"},
                "examples": [{"name": "Old Item"}],
            }
        }

        prompt_file = self.prompts_dir / "old_prompt.json"
        with open(prompt_file, "w") as f:
            json.dump(prompt_data, f)

        # Mock user choosing to edit the prompt (new workflow order)
        mock_input.side_effect = [
            "n",  # Don't use saved prompt, edit it
            "products",  # object name (now first)
            "New product records",  # object description
            "New API",  # New API name (with default shown)
            "New description",  # New API description (with default shown)
            '{"id": "integer", "name": "string", "price": "number"}',  # JSON schema (one line)
            "",  # Empty line 1
            "",  # Empty line 2
            # Example 1
            '{"id": 1, "name": "Product 1", "price": 19.99}',  # Example 1 (one line)
            "",  # Empty line 1
            "",  # Empty line 2
            # Example 2
            '{"id": 2, "name": "Product 2", "price": 29.99}',  # Example 2 (one line)
            "",  # Empty line 1
            "",  # Empty line 2
        ]

        # No need to mock API response anymore

        # Generate with edited prompt
        spec = generator.interactive_generate(prompt_file=str(prompt_file))

        assert spec["info"]["title"] == "New API"

        # Verify the spec was generated correctly
        assert spec["info"]["title"] == "New API"

    def test_prompt_filename_generation(self):
        """Test that prompt filenames are generated correctly."""
        generator = SpecGenerator()

        # Test various API names and their expected filenames
        test_cases = [
            ("Simple API", "simple_api_prompt.json"),
            ("My Complex API Name!", "my_complex_api_name_prompt.json"),
            ("API-with-dashes", "api_with_dashes_prompt.json"),
            ("API with spaces & symbols", "api_with_spaces_symbols_prompt.json"),
        ]

        for api_name, expected_filename in test_cases:
            api_info = {
                "name": api_name,
                "description": "test",
                "endpoint_descriptions": "test",
            }
            spec = {"info": {"title": api_name, "version": "1.0.0"}}

            # Call _save_prompt to generate the filename
            generator._save_prompt(api_info, spec)

            # Check that the expected file was created
            expected_path = self.prompts_dir / expected_filename
            assert (
                expected_path.exists()
            ), f"Expected {expected_filename} to be created for API name '{api_name}'"

            # Clean up for next test
            expected_path.unlink()

    @patch("builtins.input")
    def test_schema_editing_workflow(self, mock_input):
        """Test the complete schema editing workflow."""
        generator = SpecGenerator()

        # Mock user inputs for initial generation (new workflow order)
        mock_input.side_effect = [
            "tests",  # object name (now first)
            "Test records",  # object description
            "Test API",  # API name (with default shown)
            "Test description",  # API description (with default shown)
            "{",  # JSON schema start
            '  "id": "integer",',
            '  "name": "string"',
            "}",
            "",  # Empty line 1
            "",  # Empty line 2
            # JSON array examples (new format)
            "[",
            '  {"id": 1, "name": "Test 1"},',
            '  {"id": 2, "name": "Test 2"}',
            "]",
            "",  # Empty line 1
            "",  # Empty line 2
        ]

        # Generate initial spec
        generator.interactive_generate()

        # Check that both prompt and schema files were created (filename based on auto-inferred project name "tests")
        prompt_file = self.prompts_dir / "tests_prompt.json"
        schema_file = self.prompts_dir / "tests_schema.json"

        assert prompt_file.exists()
        assert schema_file.exists()

        # Load and verify the schema
        with open(schema_file) as f:
            schema = json.load(f)

        assert "endpoints" in schema
        assert "objects" in schema
        assert (
            len(schema["endpoints"]) == 5
        )  # CRUD endpoints: GET all, GET one, POST, PUT, DELETE
        assert any(endpoint["path"] == "/tests" for endpoint in schema["endpoints"])

        # Simulate user editing the schema file
        import time

        time.sleep(0.1)  # Ensure different modification time

        modified_schema = {
            "endpoints": [
                {
                    "path": "/test",
                    "method": "GET",
                    "description": "Test endpoint",
                    "returns": "object",
                },
                {
                    "path": "/users",
                    "method": "GET",
                    "description": "Get users",
                    "returns": "array of User objects",
                },
            ],
            "objects": [
                {"name": "TestObject", "fields": {"id": "integer", "name": "string"}},
                {"name": "User", "fields": {"id": "integer", "email": "string"}},
            ],
        }

        with open(schema_file, "w") as f:
            json.dump(modified_schema, f, indent=2)

        # Reset mock input for regeneration
        mock_input.side_effect = ["y"]  # Use saved prompt

        # Regenerate - should detect modified schema and use it
        regenerated_spec = generator.interactive_generate(prompt_file=str(prompt_file))

        # Verify the regenerated spec includes the new endpoint
        assert "/test" in regenerated_spec["paths"]
        assert "/users" in regenerated_spec["paths"]

        # Verify the schema modification detection works
        assert generator._schema_modified_since_prompt(str(prompt_file), schema_file)

"""Tests for CLI auto-discovery functionality."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest  # noqa: E402
import tempfile  # noqa: E402
import shutil  # noqa: E402
from unittest.mock import patch  # noqa: E402
import yaml  # noqa: E402
from automatic.cli import (  # noqa: E402, F401
    auto_discover_and_setup,
    find_api_specs,
    is_openapi_spec,
    setup_first_run,
    find_missing_implementations,
    add_missing_implementations
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


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
                    "responses": {"200": {"description": "Success"}}
                },
                "post": {
                    "operationId": "create_user",
                    "responses": {"201": {"description": "Created"}}
                }
            },
            "/users/{user_id}": {
                "get": {
                    "operationId": "get_user",
                    "parameters": [
                        {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }


class TestOpenAPIDetection:
    """Test OpenAPI spec detection."""
    
    def test_is_openapi_spec_with_openapi_field(self, temp_dir, sample_openapi_spec):
        """Test detection of OpenAPI 3.0 spec."""
        spec_file = temp_dir / "test.yaml"
        with open(spec_file, 'w') as f:
            yaml.dump(sample_openapi_spec, f)
        
        assert is_openapi_spec(spec_file) is True
    
    def test_is_openapi_spec_with_swagger_field(self, temp_dir):
        """Test detection of Swagger 2.0 spec."""
        swagger_spec = {
            "swagger": "2.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        spec_file = temp_dir / "swagger.yaml"
        with open(spec_file, 'w') as f:
            yaml.dump(swagger_spec, f)
        
        assert is_openapi_spec(spec_file) is True
    
    def test_is_openapi_spec_with_json_format(self, temp_dir):
        """Test detection of JSON OpenAPI spec."""
        spec_file = temp_dir / "test.json"
        with open(spec_file, 'w') as f:
            f.write('{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}')
        
        assert is_openapi_spec(spec_file) is True
    
    def test_is_openapi_spec_not_openapi(self, temp_dir):
        """Test rejection of non-OpenAPI files."""
        not_spec_file = temp_dir / "not_spec.yaml"
        with open(not_spec_file, 'w') as f:
            f.write("some_other_field: value\ndata: test")
        
        assert is_openapi_spec(not_spec_file) is False
    
    def test_is_openapi_spec_invalid_file(self, temp_dir):
        """Test handling of invalid files."""
        invalid_file = temp_dir / "invalid.yaml"
        with open(invalid_file, 'wb') as f:
            f.write(b'\x00\x01\x02')  # Binary data
        
        assert is_openapi_spec(invalid_file) is False


class TestSpecDiscovery:
    """Test spec file discovery."""
    
    def test_find_api_specs_empty_directory(self, temp_dir):
        """Test finding specs in empty directory."""
        specs = find_api_specs(temp_dir)
        assert specs == []
    
    def test_find_api_specs_with_valid_specs(self, temp_dir, sample_openapi_spec):
        """Test finding valid OpenAPI specs."""
        # Create valid specs
        users_spec = temp_dir / "users.yaml"
        orders_spec = temp_dir / "orders.yml"
        products_spec = temp_dir / "products.json"
        
        with open(users_spec, 'w') as f:
            yaml.dump(sample_openapi_spec, f)
        with open(orders_spec, 'w') as f:
            yaml.dump(sample_openapi_spec, f)
        with open(products_spec, 'w') as f:
            import json
            json.dump(sample_openapi_spec, f)
        
        # Create non-spec files
        (temp_dir / "readme.md").write_text("# README")
        (temp_dir / "config.yaml").write_text("database: localhost")
        
        specs = find_api_specs(temp_dir)
        
        assert len(specs) == 3
        spec_names = [spec.name for spec in specs]
        assert "users.yaml" in spec_names
        assert "orders.yml" in spec_names 
        assert "products.json" in spec_names
    
    def test_find_api_specs_ignores_non_openapi_files(self, temp_dir):
        """Test that non-OpenAPI YAML files are ignored."""
        # Create non-OpenAPI YAML file
        config_file = temp_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump({"database": "localhost", "port": 5432}, f)
        
        specs = find_api_specs(temp_dir)
        assert specs == []


class TestFirstRunSetup:
    """Test first run project setup."""
    
    @patch('automatic.cli.ScaffoldGenerator')
    def test_setup_first_run_single_spec(self, mock_generator_class, temp_dir, sample_openapi_spec):
        """Test first run setup with single spec."""
        # Create spec file
        spec_file = temp_dir / "users.yaml"
        with open(spec_file, 'w') as f:
            yaml.dump(sample_openapi_spec, f)
        
        # Mock scaffold generator
        mock_generator = mock_generator_class.return_value
        mock_generator.get_default_output_path.return_value = "implementations/user_service.py"
        mock_generator.generate_scaffold.return_value = True
        
        # Change to temp directory for the test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            setup_first_run([spec_file])
            
            # Verify scaffold generator was called
            assert mock_generator_class.called
            assert mock_generator.generate_scaffold.called
            
        finally:
            os.chdir(original_cwd)
    
    @patch('automatic.cli.ScaffoldGenerator')
    @patch('automatic.cli.create_multi_spec_main')
    @patch('automatic.cli.organize_spec_files')
    @patch('automatic.cli.create_gitignore_if_needed')
    def test_setup_first_run_multiple_specs(self, mock_gitignore, mock_organize, mock_create_main, mock_generator_class, temp_dir, sample_openapi_spec):
        """Test first run setup with multiple specs."""
        # Create multiple spec files
        users_spec = temp_dir / "users.yaml"
        orders_spec = temp_dir / "orders.yaml"
        
        for spec_file in [users_spec, orders_spec]:
            with open(spec_file, 'w') as f:
                yaml.dump(sample_openapi_spec, f)
        
        # Mock scaffold generator
        mock_generator = mock_generator_class.return_value
        mock_generator.get_default_output_path.return_value = "implementations/test_service.py"
        mock_generator.generate_scaffold.return_value = True
        
        # Store original _should_init_project method to verify it was overridden
        original_should_init = None
        
        def capture_should_init(*args, **kwargs):
            nonlocal original_should_init
            # Capture the _should_init_project method when ScaffoldGenerator is instantiated
            instance = mock_generator_class.return_value
            original_should_init = getattr(instance, '_should_init_project', None)
            return instance
        
        mock_generator_class.side_effect = capture_should_init
        
        # Change to temp directory for the test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            setup_first_run([users_spec, orders_spec])
            
            # Verify scaffold generator was called for both specs
            assert mock_generator_class.call_count == 2
            assert mock_generator.generate_scaffold.call_count == 2
            
            # Verify that _should_init_project was overridden (disabled)
            # The lambda function that always returns False should have been assigned
            assert hasattr(mock_generator, '_should_init_project')
            assert mock_generator._should_init_project() is False
            
            # Verify multi-spec setup functions were called
            mock_organize.assert_called_once()
            mock_create_main.assert_called_once()
            mock_gitignore.assert_called_once()
            
        finally:
            os.chdir(original_cwd)


class TestIncrementalMode:
    """Test incremental mode functionality."""
    
    def test_find_missing_implementations_no_specs_dir(self, temp_dir):
        """Test finding missing implementations when specs dir doesn't exist."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            missing = find_missing_implementations()
            assert missing == []
            
        finally:
            os.chdir(original_cwd)
    
    @patch('automatic.cli.ScaffoldGenerator')
    def test_find_missing_implementations_with_missing(self, mock_generator_class, temp_dir, sample_openapi_spec):
        """Test finding specs without implementations."""
        # Set up directory structure
        specifications_dir = temp_dir / "specifications"
        implementations_dir = temp_dir / "implementations"
        specifications_dir.mkdir()
        implementations_dir.mkdir()
        
        # Create spec file
        spec_file = specifications_dir / "users.yaml"
        with open(spec_file, 'w') as f:
            yaml.dump(sample_openapi_spec, f)
        
        # Mock scaffold generator to return expected path
        mock_generator = mock_generator_class.return_value
        mock_generator.get_default_output_path.return_value = "implementations/user_service.py"
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            missing = find_missing_implementations()
            
            assert len(missing) == 1
            assert missing[0].name == "users.yaml"
            
        finally:
            os.chdir(original_cwd)
    
    @patch('automatic.cli.ScaffoldGenerator')
    def test_find_missing_implementations_all_exist(self, mock_generator_class, temp_dir, sample_openapi_spec):
        """Test when all implementations exist."""
        # Set up directory structure
        specifications_dir = temp_dir / "specifications"
        implementations_dir = temp_dir / "implementations"
        specifications_dir.mkdir()
        implementations_dir.mkdir()
        
        # Create spec file
        spec_file = specifications_dir / "users.yaml"
        with open(spec_file, 'w') as f:
            yaml.dump(sample_openapi_spec, f)
        
        # Create corresponding implementation
        impl_file = implementations_dir / "user_service.py"
        impl_file.write_text("# Implementation")
        
        # Mock scaffold generator
        mock_generator = mock_generator_class.return_value
        mock_generator.get_default_output_path.return_value = str(impl_file)
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            missing = find_missing_implementations()
            assert missing == []
            
        finally:
            os.chdir(original_cwd)


class TestAutoDiscoveryModes:
    """Test the main auto-discovery mode selection."""
    
    @patch('automatic.cli.setup_first_run')
    @patch('automatic.cli.find_api_specs')
    def test_auto_discover_first_run_mode(self, mock_find_specs, mock_setup, temp_dir, sample_openapi_spec):
        """Test auto-discovery in first run mode."""
        # Mock finding specs
        spec_file = temp_dir / "users.yaml"
        mock_find_specs.return_value = [spec_file]
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            auto_discover_and_setup()
            
            # Verify first run setup was called
            mock_setup.assert_called_once_with([spec_file])
            
        finally:
            os.chdir(original_cwd)
    
    @patch('automatic.cli.add_missing_implementations')
    @patch('automatic.cli.find_missing_implementations')
    def test_auto_discover_incremental_mode(self, mock_find_missing, mock_add_missing, temp_dir):
        """Test auto-discovery in incremental mode."""
        # Set up existing project structure
        specifications_dir = temp_dir / "specifications"
        implementations_dir = temp_dir / "implementations"
        specifications_dir.mkdir()
        implementations_dir.mkdir()
        
        # Mock finding missing implementations
        missing_spec = temp_dir / "specifications" / "new_api.yaml"
        mock_find_missing.return_value = [missing_spec]
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            auto_discover_and_setup()
            
            # Verify incremental mode was used
            mock_add_missing.assert_called_once_with([missing_spec])
            
        finally:
            os.chdir(original_cwd)
    
    @patch('automatic.cli.find_missing_implementations')
    def test_auto_discover_incremental_mode_no_missing(self, mock_find_missing, temp_dir, capsys):
        """Test auto-discovery when no implementations are missing."""
        # Set up existing project structure
        specifications_dir = temp_dir / "specifications"
        implementations_dir = temp_dir / "implementations"
        specifications_dir.mkdir()
        implementations_dir.mkdir()
        
        # Mock no missing implementations
        mock_find_missing.return_value = []
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            auto_discover_and_setup()
            
            # Check output message
            captured = capsys.readouterr()
            assert "All specifications have corresponding implementations" in captured.out
            
        finally:
            os.chdir(original_cwd)
    
    @patch('automatic.cli.find_api_specs')
    def test_auto_discover_no_specs_found(self, mock_find_specs, temp_dir, capsys):
        """Test auto-discovery when no specs are found."""
        # Mock no specs found
        mock_find_specs.return_value = []
        
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            auto_discover_and_setup()
            
            # Check output message
            captured = capsys.readouterr()
            assert "No OpenAPI specification files found" in captured.out
            
        finally:
            os.chdir(original_cwd)


class TestMainPyGeneration:
    """Test main.py generation with correct spec paths."""
    
    def test_main_py_uses_versioned_spec_paths(self, temp_dir):
        """Test that generated main.py references versioned spec files."""
        from pathlib import Path
        from automatic.cli import create_multi_spec_main
        
        # Create mock spec files
        users_spec = temp_dir / "users.yaml"
        orders_spec = temp_dir / "orders.yaml"
        
        # Create minimal OpenAPI content
        sample_spec = {
            'openapi': '3.0.0',
            'info': {'title': 'Test API', 'version': '1.0.0'},
            'paths': {'/test': {'get': {'operationId': 'test_endpoint'}}}
        }
        
        import yaml
        for spec_file in [users_spec, orders_spec]:
            with open(spec_file, 'w') as f:
                yaml.dump(sample_spec, f)
        
        # Change to temp directory and test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(temp_dir)
            
            # Create the multi-spec main.py
            create_multi_spec_main([users_spec, orders_spec])
            
            # Read generated main.py
            main_py = temp_dir / "main.py"
            assert main_py.exists(), "main.py should be created"
            
            main_content = main_py.read_text()
            
            # Verify versioned spec paths are used (not original names)
            assert 'specifications/users_v1.yaml' in main_content, "Should reference users_v1.yaml"
            assert 'specifications/orders_v1.yaml' in main_content, "Should reference orders_v1.yaml"
            
            # Verify original names are NOT used
            assert 'specifications/users.yaml' not in main_content, "Should not reference unversioned users.yaml"
            assert 'specifications/orders.yaml' not in main_content, "Should not reference unversioned orders.yaml"
            
            # Verify comments also use versioned names
            assert '# users_v1.yaml' in main_content, "Comments should reference versioned files"
            assert '# orders_v1.yaml' in main_content, "Comments should reference versioned files"
            
        finally:
            os.chdir(original_cwd)
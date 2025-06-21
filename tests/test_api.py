"""Tests for automatic API discovery functionality."""

import pytest
import tempfile
import os
from pathlib import Path

import automatic


def test_automatic_discovery():
    """Test that automatic file discovery works correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create directory structure
        api_dir = temp_path / "specifications"
        impl_dir = temp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()
        
        # Create test spec file
        test_spec = api_dir / "test.yaml"
        test_spec.write_text("""
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /:
    get:
      operationId: test_method
      responses:
        '200':
          description: Success
""")
        
        # Create test implementation file
        test_impl = impl_dir / "test.py"
        test_impl.write_text("""
class Implementation:
    def test_method(self, data):
        return {"message": "test"}, 200
""")
        
        # Change to temp directory and create app
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            app = automatic.create_app()
            
            # Check that routes were created with prefix
            routes = [route for route in app.routes 
                     if hasattr(route, 'path') and route.path.startswith('/test')]
            
            assert len(routes) == 1
            assert routes[0].path == "/test/"
            assert "GET" in routes[0].methods
            
        finally:
            os.chdir(original_cwd)


def test_api_with_custom_directories():
    """Test automatic discovery with custom directory names."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create custom directory structure
        specs_dir = temp_path / "specs"
        handlers_dir = temp_path / "handlers"
        specs_dir.mkdir()
        handlers_dir.mkdir()
        
        # Create test files
        test_spec = specs_dir / "custom.yaml"
        test_spec.write_text("""
openapi: 3.0.0
info:
  title: Custom API
  version: 1.0.0
paths:
  /hello:
    get:
      operationId: say_hello
      responses:
        '200':
          description: Success
""")
        
        test_impl = handlers_dir / "custom.py"
        test_impl.write_text("""
class Implementation:
    def say_hello(self, data):
        return {"message": "hello"}, 200
""")
        
        # Change to temp directory and create app with custom dirs
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            app = automatic.create_app(api_dir="specs", impl_dir="handlers")
            
            # Check that routes were created
            routes = [route for route in app.routes 
                     if hasattr(route, 'path') and route.path.startswith('/custom')]
            
            assert len(routes) == 1
            assert routes[0].path == "/custom/hello"
            
        finally:
            os.chdir(original_cwd)


def test_missing_implementation_class_error():
    """Test that missing Implementation class raises appropriate error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create directory structure
        api_dir = temp_path / "specifications"
        impl_dir = temp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()
        
        # Create spec file
        test_spec = api_dir / "bad.yaml"
        test_spec.write_text("""
openapi: 3.0.0
info:
  title: Bad API
  version: 1.0.0
paths:
  /:
    get:
      operationId: test_method
      responses:
        '200':
          description: Success
""")
        
        # Create implementation file without Implementation class
        test_impl = impl_dir / "bad.py"
        test_impl.write_text("""
class WrongClassName:
    def test_method(self, data):
        return {"message": "test"}, 200
""")
        
        # Should raise error about missing Implementation class
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with pytest.raises(AttributeError, match="No 'Implementation' class found"):
                automatic.create_app()
        finally:
            os.chdir(original_cwd)


def test_no_matching_files_error():
    """Test that having no matching spec/impl pairs raises error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create empty directories
        api_dir = temp_path / "specifications"
        impl_dir = temp_path / "implementations"
        api_dir.mkdir()
        impl_dir.mkdir()
        
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with pytest.raises(ValueError, match="No matching spec/implementation pairs found"):
                automatic.create_app()
        finally:
            os.chdir(original_cwd)
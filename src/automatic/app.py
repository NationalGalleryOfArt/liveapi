"""Main application interface for automatic framework."""

from typing import Union, Any, Optional
from pathlib import Path
from fastapi import FastAPI
import importlib.util
import glob
from .parser import OpenAPIParser
from .router import RouteGenerator


def create_app(
    spec_path: Optional[Union[str, Path]] = None, 
    implementation: Optional[Any] = None,
    api_dir: Union[str, Path] = "api",
    impl_dir: Union[str, Path] = "implementations",
    **kwargs
) -> FastAPI:
    """
    Create a FastAPI application from OpenAPI specifications and implementations.
    
    Two modes:
    1. Single spec mode (legacy): provide spec_path and implementation
    2. Convention mode (new): uses api_dir and impl_dir with file discovery
    
    Args:
        spec_path: Path to single OpenAPI spec file (for legacy mode)
        implementation: Implementation class (for legacy mode)
        api_dir: Directory containing *.yaml spec files (default: "api")
        impl_dir: Directory containing implementation *.py files (default: "implementations")
        **kwargs: Additional arguments to pass to FastAPI constructor
    
    Returns:
        Configured FastAPI application
    
    Examples:
        >>> # Legacy mode
        >>> app = create_app("api.yaml", MyImplementation())
        
        >>> # Convention mode (zero config)
        >>> app = create_app()
        
        >>> # Convention mode with custom directories
        >>> app = create_app(api_dir="./specs", impl_dir="./handlers")
    """
    # Legacy single-spec mode
    if spec_path is not None and implementation is not None:
        return _create_single_spec_app(spec_path, implementation, **kwargs)
    
    # Convention-based mode
    return _create_convention_app(api_dir, impl_dir, **kwargs)


def _create_single_spec_app(spec_path: Union[str, Path], implementation: Any, **kwargs) -> FastAPI:
    """Create app from single spec file (legacy mode)."""
    # Parse OpenAPI specification
    parser = OpenAPIParser(spec_path)
    parser.load_spec()
    
    # Extract app metadata from spec
    info = parser.spec.get('info', {})
    
    # Create FastAPI app with metadata from OpenAPI spec
    app_kwargs = {
        'title': info.get('title', 'Automatic API'),
        'description': info.get('description', ''),
        'version': info.get('version', '1.0.0'),
    }
    app_kwargs.update(kwargs)
    
    app = FastAPI(**app_kwargs)
    
    # Generate and add routes
    route_generator = RouteGenerator(implementation)
    routes = route_generator.generate_routes(parser)
    
    for route in routes:
        app.router.routes.append(route)
    
    return app


def _create_convention_app(api_dir: Union[str, Path], impl_dir: Union[str, Path], **kwargs) -> FastAPI:
    """Create app using convention-based file discovery."""
    api_path = Path(api_dir)
    impl_path = Path(impl_dir)
    
    # Create FastAPI app
    app_kwargs = {
        'title': 'Automatic API',
        'description': 'Convention-based API from automatic framework',
        'version': '1.0.0',
    }
    app_kwargs.update(kwargs)
    
    app = FastAPI(**app_kwargs)
    
    # Discover spec/implementation pairs
    spec_impl_pairs = _discover_spec_impl_pairs(api_path, impl_path)
    
    if not spec_impl_pairs:
        raise ValueError(f"No matching spec/implementation pairs found in {api_path} and {impl_path}")
    
    # Process each pair
    for spec_file, impl_file, prefix in spec_impl_pairs:
        # Load implementation
        implementation = _load_implementation(impl_file)
        
        # Parse OpenAPI spec
        parser = OpenAPIParser(spec_file)
        parser.load_spec()
        
        # Generate routes with prefix
        route_generator = RouteGenerator(implementation, path_prefix=prefix)
        routes = route_generator.generate_routes(parser)
        
        for route in routes:
            app.router.routes.append(route)
    
    return app


def _discover_spec_impl_pairs(api_dir: Path, impl_dir: Path):
    """Discover matching spec and implementation file pairs."""
    if not api_dir.exists():
        raise FileNotFoundError(f"API directory not found: {api_dir}")
    
    if not impl_dir.exists():
        raise FileNotFoundError(f"Implementation directory not found: {impl_dir}")
    
    pairs = []
    
    # Find all YAML files in api directory
    yaml_files = list(api_dir.glob("*.yaml")) + list(api_dir.glob("*.yml"))
    
    for yaml_file in yaml_files:
        # Get base name (without extension)
        base_name = yaml_file.stem
        
        # Look for matching Python file
        py_file = impl_dir / f"{base_name}.py"
        
        if py_file.exists():
            # Use base name as path prefix (e.g., users.yaml -> /users)
            prefix = f"/{base_name}"
            pairs.append((yaml_file, py_file, prefix))
    
    return pairs


def _load_implementation(impl_file: Path):
    """Load Implementation class from a Python file."""
    spec = importlib.util.spec_from_file_location("implementation_module", impl_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load implementation from {impl_file}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Look for standard Implementation class
    if not hasattr(module, 'Implementation'):
        raise AttributeError(f"No 'Implementation' class found in {impl_file}")
    
    implementation_class = getattr(module, 'Implementation')
    return implementation_class()


class AutomaticApp:
    """
    Alternative class-based interface for the automatic framework.
    
    Example:
        >>> class MyImplementation:
        ...     def create_art_object(self, data):
        ...         return {"id": 1, "title": data["title"]}, 201
        >>> 
        >>> automatic_app = AutomaticApp("api.yaml", MyImplementation())
        >>> app = automatic_app.create_fastapi_app()
    """
    
    def __init__(self, spec_path: Union[str, Path], implementation: Any):
        self.spec_path = spec_path
        self.implementation = implementation
        self.parser = None
        self.route_generator = None
        
    def load_spec(self):
        """Load and parse the OpenAPI specification."""
        self.parser = OpenAPIParser(self.spec_path)
        self.parser.load_spec()
        return self.parser
    
    def create_fastapi_app(self, **kwargs) -> FastAPI:
        """Create a FastAPI application."""
        return create_app(self.spec_path, self.implementation, **kwargs)
    
    def get_routes_info(self):
        """Get information about all routes that will be generated."""
        if not self.parser:
            self.load_spec()
        
        routes = self.parser.get_routes()
        return [{
            'path': route['path'],
            'method': route['method'],
            'operation_id': route['operation_id'],
            'summary': route['summary']
        } for route in routes]
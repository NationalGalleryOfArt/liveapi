"""Main application interface for automatic framework."""

from typing import Union, Any
from pathlib import Path
from fastapi import FastAPI
from .parser import OpenAPIParser
from .router import RouteGenerator


def create_app(spec_path: Union[str, Path], implementation: Any, **kwargs) -> FastAPI:
    """
    Create a FastAPI application from an OpenAPI specification and implementation.
    
    Args:
        spec_path: Path to the OpenAPI specification file (YAML or JSON)
        implementation: Implementation class with methods matching operationIds
        **kwargs: Additional arguments to pass to FastAPI constructor
    
    Returns:
        Configured FastAPI application
    
    Example:
        >>> class MyImplementation:
        ...     def create_art_object(self, data):
        ...         return {"id": 1, "title": data["title"]}, 201
        >>> 
        >>> app = create_app("api.yaml", MyImplementation())
    """
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
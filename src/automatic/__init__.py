"""
Automatic - Runtime OpenAPI to FastAPI. No code generation.

A Python framework that dynamically creates FastAPI routes from OpenAPI 
specifications at runtime, eliminating code generation.
"""

from .app import create_app, AutomaticApp
from .parser import OpenAPIParser
from .router import RouteGenerator

__version__ = "0.1.0"
__all__ = ["create_app", "AutomaticApp", "OpenAPIParser", "RouteGenerator"]
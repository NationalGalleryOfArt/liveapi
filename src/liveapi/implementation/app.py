"""Main application interface for LiveAPI CRUD+ framework."""

from typing import Union
from pathlib import Path
from fastapi import FastAPI
from .liveapi_router import create_liveapi_app


def create_app(spec_path: Union[str, Path]) -> FastAPI:
    """
    Create a FastAPI application from OpenAPI specification using CRUD+ handlers.

    Args:
        spec_path: Path to OpenAPI specification file

    Returns:
        FastAPI application with CRUD+ endpoints

    Example:
        >>> app = create_app("specifications/users_v1.yaml")
    """
    return create_liveapi_app(spec_path)

"""Main application interface for LiveAPI CRUD+ framework."""

from typing import Union
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .liveapi_router import create_liveapi_app
from .exceptions import BusinessException, InternalServerError


def add_exception_handlers(app: FastAPI):
    """Add custom exception handlers to the FastAPI app."""

    @app.exception_handler(BusinessException)
    async def handle_business_exception(request: Request, exc: BusinessException):
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        # Log the exception for debugging
        # Return a generic 500 error
        server_error = InternalServerError(
            "An unexpected error occurred. Please contact support."
        )
        return JSONResponse(
            status_code=server_error.status_code, content=server_error.to_response()
        )


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
    app = create_liveapi_app(spec_path)
    add_exception_handlers(app)
    return app

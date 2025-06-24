"""Main application interface for LiveAPI CRUD+ framework."""

from typing import Union
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .liveapi_router import create_liveapi_app
from .exceptions import (
    BusinessException,
    InternalServerError,
    NotImplementedError as CustomNotImplementedError,
)


def add_exception_handlers(app: FastAPI):
    """Add custom exception handlers to the FastAPI app."""

    @app.exception_handler(BusinessException)
    async def handle_business_exception(request: Request, exc: BusinessException):
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())

    @app.exception_handler(NotImplementedError)
    async def handle_not_implemented_error(request: Request, exc: NotImplementedError):
        # Convert built-in NotImplementedError to our custom format
        custom_exc = CustomNotImplementedError(
            str(exc) or "This feature is not yet implemented."
        )
        return JSONResponse(
            status_code=custom_exc.status_code, content=custom_exc.to_response()
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        # If this is a test, we want to see the actual exception
        if "pytest" in str(request.scope.get("client", "")):
            raise exc

        # Log the exception for debugging
        # Return a generic 500 error
        server_error = InternalServerError("An unexpected error occurred.")
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

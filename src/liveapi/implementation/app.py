"""Main application interface for LiveAPI CRUD+ framework."""

from typing import Union
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .liveapi_router import (
    create_liveapi_app,
    add_error_schemas_to_app,
    create_rfc7807_validation_error_handler,
)
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

    # Add RFC 7807 validation error handler for 422 responses
    app.add_exception_handler(
        RequestValidationError, create_rfc7807_validation_error_handler()
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


def create_app(*spec_paths: Union[str, Path]) -> FastAPI:
    """
    Create a FastAPI application from OpenAPI specification(s) using CRUD+ handlers.

    Args:
        *spec_paths: Path(s) to OpenAPI specification file(s)

    Returns:
        FastAPI application with CRUD+ endpoints

    Example:
        >>> app = create_app("specifications/users_v1.yaml")
        >>> app = create_app("specifications/users.json", "specifications/orders.json")
    """
    app = create_liveapi_app(*spec_paths)
    add_exception_handlers(app)
    add_error_schemas_to_app(app)
    return app

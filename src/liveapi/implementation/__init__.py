"""
LiveAPI Implementation - Opinionated CRUD+ API Engine

A focused framework for building standardized CRUD+ APIs from OpenAPI specifications.
"""

from .app import create_app
from .crud_handlers import CRUDHandlers, create_crud_router
from .pydantic_generator import PydanticGenerator
from .liveapi_parser import LiveAPIParser
from .liveapi_router import LiveAPIRouter, create_liveapi_app
from .exceptions import (
    BusinessException,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
)

__version__ = "0.2.0"
__all__ = [
    "create_app",
    "CRUDHandlers",
    "create_crud_router",
    "PydanticGenerator",
    "LiveAPIParser",
    "LiveAPIRouter",
    "create_liveapi_app",
    "BusinessException",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
]

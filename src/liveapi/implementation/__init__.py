"""
LiveAPI Implementation - Opinionated CRUD+ API Engine

A focused framework for building standardized CRUD+ APIs from OpenAPI specifications.
"""

from .app import create_app
from .default_resource import DefaultResource, create_resource_router
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
    "DefaultResource",
    "create_resource_router",
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

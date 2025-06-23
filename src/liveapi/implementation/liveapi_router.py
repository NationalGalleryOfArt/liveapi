"""LiveAPI router that maps CRUD+ resources to standard handlers."""

from typing import Dict, Any, List, Type
from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .liveapi_parser import LiveAPIParser
from .default_resource_service import DefaultResourceService
from .exceptions import BusinessException

# Auth removed - handled at API Gateway level


def create_business_exception_handler():
    """Create a handler for business exceptions that returns RFC 7807 format."""

    async def business_exception_handler(request: Request, exc: BusinessException):
        """Convert business exceptions to RFC 7807 format."""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_response(),
            headers={"Content-Type": "application/problem+json"},
        )

    return business_exception_handler


def create_rfc7807_validation_error_handler():
    """Create a custom validation error handler that returns RFC 7807 format."""

    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Convert FastAPI validation errors to RFC 7807 format."""
        errors = []

        for error in exc.errors():
            # Extract location information
            loc = error.get("loc", [])
            field_path = "/".join(str(item) for item in loc if item != "body")

            # Create RFC 7807 compliant error
            rfc_error = {
                "title": "Unprocessable Entity",
                "detail": error.get("msg", "Validation error"),
                "status": "422",
                "source": {
                    "pointer": (
                        f"/data/attributes/{field_path}" if field_path else "/data"
                    )
                },
            }
            errors.append(rfc_error)

        return JSONResponse(
            status_code=422,
            content={"errors": errors},
            headers={"Content-Type": "application/problem+json"},
        )

    return validation_exception_handler


class LiveAPIRouter:
    """Router that creates CRUD+ endpoints using standard handlers.

    This router identifies CRUD+ resources in OpenAPI specs and automatically
    creates endpoints using the standard DefaultResourceService.
    """

    def __init__(self):
        self.routers: Dict[str, APIRouter] = {}
        self.handlers: Dict[str, DefaultResourceService] = {}

    def create_app_from_spec(self, spec_path: str) -> FastAPI:
        """Create a FastAPI app from an OpenAPI spec using CRUD+ handlers.

        Args:
            spec_path: Path to OpenAPI specification

        Returns:
            FastAPI app with CRUD+ endpoints
        """
        # Parse the spec
        parser = LiveAPIParser(spec_path)
        parser.load_spec()

        # Create FastAPI app
        app = FastAPI(
            title=parser.spec.get("info", {}).get("title", "LiveAPI CRUD+ API"),
            description=parser.spec.get("info", {}).get("description", ""),
            version=parser.spec.get("info", {}).get("version", "1.0.0"),
        )

        # Add custom exception handlers for RFC 7807 compliance
        app.add_exception_handler(
            RequestValidationError, create_rfc7807_validation_error_handler()
        )
        app.add_exception_handler(
            BusinessException, create_business_exception_handler()
        )

        # Override OpenAPI schema to use correct validation error format
        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema

            # Import get_openapi to avoid recursion
            from fastapi.openapi.utils import get_openapi

            # Get the default OpenAPI schema using FastAPI's function directly
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )

            # Add our custom ValidationError schema
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            if "schemas" not in openapi_schema["components"]:
                openapi_schema["components"]["schemas"] = {}

            # Replace the default ValidationError with our RFC 7807 format
            openapi_schema["components"]["schemas"]["ValidationError"] = {
                "type": "object",
                "properties": {
                    "errors": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "detail": {"type": "string"},
                                "status": {"type": "string"},
                                "source": {
                                    "type": "object",
                                    "properties": {"pointer": {"type": "string"}},
                                },
                            },
                            "required": ["title", "detail", "status"],
                        },
                    }
                },
                "required": ["errors"],
            }

            # Override 422 responses to use our ValidationError schema
            for path_item in openapi_schema.get("paths", {}).values():
                for operation in path_item.values():
                    if isinstance(operation, dict) and "responses" in operation:
                        if "422" in operation["responses"]:
                            operation["responses"]["422"] = {
                                "description": "Validation Error",
                                "content": {
                                    "application/problem+json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ValidationError"
                                        }
                                    }
                                },
                            }

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi

        # Identify CRUD resources
        resources = parser.identify_crud_resources()

        # Create routers for each resource
        for resource_name, resource_info in resources.items():
            model = resource_info["model"]
            if model:
                router = self._create_resource_router(
                    resource_name, resource_info, model
                )
                app.include_router(router, tags=[resource_name])
                self.routers[resource_name] = router

        # Add health check
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "service": "liveapi.implementation",
                "resources": list(resources.keys()),
            }

        return app

    def _create_resource_router(
        self, resource_name: str, resource_info: Dict[str, Any], model: Type[BaseModel]
    ) -> APIRouter:
        """Create a router for a CRUD+ resource.

        Args:
            resource_name: Name of the resource
            resource_info: Resource metadata from parser
            model: Pydantic model for the resource

        Returns:
            APIRouter with CRUD+ endpoints
        """
        router = APIRouter()
        handlers = DefaultResourceService(model, resource_name)
        self.handlers[resource_name] = handlers

        # Get paths
        collection_path = resource_info["paths"]["collection"] or f"/{resource_name}"
        item_path = resource_info["paths"]["item"] or f"/{resource_name}/{{id}}"

        # Authentication removed - handled at API Gateway level

        # Map operations to handlers
        operations = resource_info["operations"]

        # Create
        if "create" in operations:
            op = operations["create"]["operation"]

            @router.post(
                collection_path,
                summary=op.get("summary", f"Create {resource_name}"),
                description=op.get("description", ""),
                response_model=model,
                status_code=201,
                operation_id=op.get("operationId", f"create_{resource_name}"),
            )
            async def create_resource(data: model):
                return await handlers.create(data.model_dump())

        # Read
        if "read" in operations:
            op = operations["read"]["operation"]

            @router.get(
                item_path,
                summary=op.get("summary", f"Get {resource_name} by ID"),
                description=op.get("description", ""),
                response_model=model,
                operation_id=op.get("operationId", f"get_{resource_name}"),
            )
            async def read_resource(id: str):
                return await handlers.read(id)

        # Update (PUT)
        if "update" in operations:
            op = operations["update"]["operation"]

            @router.put(
                item_path,
                summary=op.get("summary", f"Update {resource_name}"),
                description=op.get("description", ""),
                response_model=model,
                operation_id=op.get("operationId", f"update_{resource_name}"),
            )
            async def update_resource(id: str, data: model):
                return await handlers.update(id, data.model_dump(), partial=False)

        # Update (PATCH)
        if "update_partial" in operations:
            op = operations["update_partial"]["operation"]

            @router.patch(
                item_path,
                summary=op.get("summary", f"Partially update {resource_name}"),
                description=op.get("description", ""),
                response_model=model,
                operation_id=op.get("operationId", f"patch_{resource_name}"),
            )
            async def patch_resource(id: str, data: Dict[str, Any]):
                return await handlers.update(id, data, partial=True)

        # Delete
        if "delete" in operations:
            op = operations["delete"]["operation"]

            @router.delete(
                item_path,
                summary=op.get("summary", f"Delete {resource_name}"),
                description=op.get("description", ""),
                status_code=204,
                operation_id=op.get("operationId", f"delete_{resource_name}"),
            )
            async def delete_resource(id: str):
                await handlers.delete(id)
                return None

        # List
        if "list" in operations:
            op = operations["list"]["operation"]

            # Extract query parameters from operation
            # parameters = op.get("parameters", [])
            # query_params = {p["name"]: p for p in parameters if p.get("in") == "query"}

            @router.get(
                collection_path,
                summary=op.get("summary", f"List {resource_name}"),
                description=op.get("description", ""),
                response_model=List[model],
                operation_id=op.get("operationId", f"list_{resource_name}"),
            )
            async def list_resources(limit: int = 100, offset: int = 0):
                return await handlers.list(limit=limit, offset=offset)

        return router


def create_liveapi_app(spec_path: str) -> FastAPI:
    """Convenience function to create a LiveAPI app from a spec.

    Args:
        spec_path: Path to OpenAPI specification

    Returns:
        FastAPI app with CRUD+ endpoints
    """
    router = LiveAPIRouter()
    return router.create_app_from_spec(spec_path)

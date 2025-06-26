"""LiveAPI router that maps CRUD+ resources to standard handlers."""

from typing import Dict, Any, List, Type, Union
from pathlib import Path
from fastapi import APIRouter, FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session
from .liveapi_parser import LiveAPIParser
from .default_resource import DefaultResource
from .exceptions import BusinessException
from .database import get_db_session


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    resources: List[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "service": "liveapi.implementation",
                "resources": ["art_objects", "art_locations"],
            }
        }
    }


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
            loc = error.get("loc", [])
            field_path = "/".join(str(item) for item in loc if item != "body")

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
    """Router that creates CRUD+ endpoints using standard handlers."""

    def __init__(self):
        self.routers: Dict[str, APIRouter] = {}
        self.handlers: Dict[str, Union[DefaultResource, Any]] = {}
        self.backend_type = self._load_backend_config()

    def _load_backend_config(self) -> str:
        """Load backend configuration from project metadata."""
        try:
            project_root = Path.cwd()
            metadata_dir = project_root / ".liveapi"
            config_file = metadata_dir / "config.json"

            if config_file.exists():
                import json

                with open(config_file, "r") as f:
                    config_data = json.load(f)
                    return config_data.get("backend_type", "default")
        except Exception:
            pass
        return "default"

    def _load_project_config(self) -> Dict[str, str]:
        """Load project configuration for composite API metadata."""
        try:
            project_root = Path.cwd()
            metadata_dir = project_root / ".liveapi"
            config_file = metadata_dir / "config.json"

            if config_file.exists():
                import json

                with open(config_file, "r") as f:
                    config_data = json.load(f)
                    return {
                        "project_name": config_data.get("project_name", "LiveAPI"),
                        "base_url": config_data.get(
                            "base_url", "http://localhost:8000"
                        ),
                    }
        except Exception:
            pass
        return {"project_name": "LiveAPI", "base_url": "http://localhost:8000"}

    def _create_service_dependency(self, model: Type[BaseModel], resource_name: str):
        """Create a dependency factory for the appropriate service."""
        if self.backend_type == "sqlmodel":
            try:
                from .sql_model_resource import SQLModelResource

                def get_sql_service(session: Session = Depends(get_db_session)):
                    return SQLModelResource(
                        model=model, resource_name=resource_name, session=session
                    )

                return get_sql_service
            except ImportError:
                print("⚠️ SQLModel backend not available, falling back to default")
                # Create a singleton service instance for default backend
                if resource_name not in self.handlers:
                    self.handlers[resource_name] = DefaultResource(
                        model=model, resource_name=resource_name
                    )

                def get_default_service():
                    return self.handlers[resource_name]

                return get_default_service
        else:
            # Create a singleton service instance for default backend
            if resource_name not in self.handlers:
                self.handlers[resource_name] = DefaultResource(
                    model=model, resource_name=resource_name
                )

            def get_default_service():
                return self.handlers[resource_name]

            return get_default_service

    def create_app_from_spec(self, spec_path: str) -> FastAPI:
        """Create a FastAPI app from an OpenAPI spec using CRUD+ handlers."""
        parser = LiveAPIParser(spec_path, backend_type=self.backend_type)
        parser.load_spec()

        app = FastAPI(
            title=parser.spec.get("info", {}).get("title", "LiveAPI CRUD+ API"),
            description=parser.spec.get("info", {}).get("description", ""),
            version=parser.spec.get("info", {}).get("version", "1.0.0"),
        )

        # Store the original spec in the app instance for reference
        app.original_spec = parser.spec

        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema
            from fastapi.openapi.utils import get_openapi

            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            if "schemas" not in openapi_schema["components"]:
                openapi_schema["components"]["schemas"] = {}

            # Add standard schemas from the original spec
            if (
                hasattr(app, "original_spec")
                and "components" in app.original_spec
                and "schemas" in app.original_spec["components"]
            ):
                for schema_name, schema in app.original_spec["components"][
                    "schemas"
                ].items():
                    if schema_name not in openapi_schema["components"]["schemas"]:
                        openapi_schema["components"]["schemas"][schema_name] = schema

            # Add ValidationError schema
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

            # Remove FastAPI's default HTTPValidationError schema if it exists
            if "HTTPValidationError" in openapi_schema["components"]["schemas"]:
                del openapi_schema["components"]["schemas"]["HTTPValidationError"]

            # Add Error schema if not already present
            if "Error" not in openapi_schema["components"]["schemas"]:
                openapi_schema["components"]["schemas"]["Error"] = {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "title": {"type": "string"},
                        "status": {"type": "integer"},
                        "detail": {"type": "string"},
                    },
                    "required": ["type", "title", "status", "detail"],
                }

            # Process paths and operations
            for path, path_item in openapi_schema.get("paths", {}).items():
                # Check if this path exists in the original spec
                original_path_item = (
                    app.original_spec.get("paths", {}).get(path, {})
                    if hasattr(app, "original_spec")
                    else {}
                )

                for method, operation in path_item.items():
                    if isinstance(operation, dict) and "responses" in operation:
                        # Get original operation responses if available
                        original_operation = original_path_item.get(method, {})
                        original_responses = (
                            original_operation.get("responses", {})
                            if original_operation
                            else {}
                        )

                        # Add standard error responses from original spec
                        for status_code in ["400", "401", "500", "503"]:
                            if (
                                status_code in original_responses
                                and status_code not in operation["responses"]
                            ):
                                operation["responses"][status_code] = (
                                    original_responses[status_code]
                                )

                        # Add validation error response for operations that accept request bodies
                        if method.lower() in ["post", "put", "patch"]:
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
                        # Remove FastAPI's default 422 responses from GET and DELETE operations
                        elif (
                            method.lower() in ["get", "delete"]
                            and "422" in operation["responses"]
                        ):
                            del operation["responses"]["422"]

            # Replace any HTTPValidationError references with ValidationError
            import json

            openapi_str = json.dumps(openapi_schema)
            openapi_str = openapi_str.replace(
                '"#/components/schemas/HTTPValidationError"',
                '"#/components/schemas/ValidationError"',
            )
            openapi_schema = json.loads(openapi_str)

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi

        resources = parser.identify_crud_resources()
        for resource_name, resource_info in resources.items():
            model = resource_info["model"]
            if model:
                router = self._create_resource_router(
                    resource_name, resource_info, model
                )
                app.include_router(router, tags=[resource_name])
                self.routers[resource_name] = router

        # Initialize database after all models are created (SQLModel needs this)
        if self.backend_type == "sqlmodel":
            from .database import init_database

            init_database()

        @app.get(
            "/health",
            response_model=HealthResponse,
            responses={
                200: {
                    "description": "Health check successful",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "healthy",
                                "service": "liveapi.implementation",
                                "resources": ["art_objects", "art_locations"],
                            }
                        }
                    },
                }
            },
        )
        async def health_check():
            return {
                "status": "healthy",
                "service": "liveapi.implementation",
                "resources": list(resources.keys()),
            }

        return app

    def create_app_from_specs(self, *spec_paths: str) -> FastAPI:
        """Create a FastAPI app from multiple OpenAPI specs using CRUD+ handlers."""
        if len(spec_paths) == 1:
            return self.create_app_from_spec(spec_paths[0])

        # For multiple specs, merge them into a composite spec
        all_parsers = []
        all_resources = {}

        # Load all specs and collect resources
        for spec_path in spec_paths:
            parser = LiveAPIParser(spec_path, backend_type=self.backend_type)
            parser.load_spec()
            all_parsers.append(parser)

            # Collect resources from this spec
            resources = parser.identify_crud_resources()
            all_resources.update(resources)

        # Get project configuration for composite API metadata
        project_config = self._load_project_config()
        project_name = project_config["project_name"]
        base_url = project_config["base_url"]

        # Create app with project-specific info
        first_spec = all_parsers[0].spec if all_parsers else {}
        app = FastAPI(
            title=project_name,
            description=f"Live API Composite API for {base_url}",
            version="1.0.0",
        )

        # Store combined spec info for health endpoint
        app.original_spec = first_spec

        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema
            from fastapi.openapi.utils import get_openapi

            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            if "schemas" not in openapi_schema["components"]:
                openapi_schema["components"]["schemas"] = {}

            # Merge schemas from all specs
            for parser in all_parsers:
                if (
                    "components" in parser.spec
                    and "schemas" in parser.spec["components"]
                ):
                    for schema_name, schema in parser.spec["components"][
                        "schemas"
                    ].items():
                        if schema_name not in openapi_schema["components"]["schemas"]:
                            openapi_schema["components"]["schemas"][
                                schema_name
                            ] = schema

            # Process paths and operations for all specs
            for path, path_item in openapi_schema.get("paths", {}).items():
                for method, operation in path_item.items():
                    if isinstance(operation, dict) and "responses" in operation:
                        # Add validation error response for operations that accept request bodies
                        if method.lower() in ["post", "put", "patch"]:
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
                        # Remove FastAPI's default 422 responses from GET and DELETE operations
                        elif (
                            method.lower() in ["get", "delete"]
                            and "422" in operation["responses"]
                        ):
                            del operation["responses"]["422"]

            # Add ValidationError schema
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

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi

        # Initialize database if using sqlmodel backend
        if self.backend_type == "sqlmodel":
            from .database import init_database

            init_database()

        # Add health endpoint
        @app.get(
            "/health",
            response_model=HealthResponse,
            responses={
                200: {
                    "description": "Health check successful",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "healthy",
                                "service": "liveapi.implementation",
                                "resources": ["art_objects", "art_locations"],
                            }
                        }
                    },
                }
            },
        )
        async def health_check():
            return {
                "status": "healthy",
                "service": "liveapi.implementation",
                "resources": list(all_resources.keys()),
            }

        # Add routers for all resources from all specs
        for resource_name, resource_info in all_resources.items():
            model = resource_info["model"]
            router = self._create_resource_router(resource_name, resource_info, model)
            app.include_router(router, tags=[resource_name])

        return app

    def _create_resource_router(
        self, resource_name: str, resource_info: Dict[str, Any], model: Type[BaseModel]
    ) -> APIRouter:
        """Create a router for a CRUD+ resource."""
        router = APIRouter()
        service_dependency = self._create_service_dependency(model, resource_name)

        collection_path = resource_info["paths"]["collection"] or f"/{resource_name}"
        item_path = resource_info["paths"]["item"] or f"/{resource_name}/{{id}}"

        operations = resource_info["operations"]

        # Common error responses to be added to all endpoints
        error_responses = {
            400: {
                "description": "Bad Request",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Error"},
                        "example": {
                            "type": "https://tools.ietf.org/html/rfc7807",
                            "title": "Bad Request",
                            "status": 400,
                            "detail": "The request could not be processed due to invalid input",
                        },
                    }
                },
            },
            401: {
                "description": "Unauthorized",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Error"},
                        "example": {
                            "type": "https://tools.ietf.org/html/rfc7807",
                            "title": "Unauthorized",
                            "status": 401,
                            "detail": "Authentication credentials were missing or invalid",
                        },
                    }
                },
            },
            404: {
                "description": "Not Found",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Error"},
                        "example": {
                            "type": "https://tools.ietf.org/html/rfc7807",
                            "title": "Not Found",
                            "status": 404,
                            "detail": "The requested resource was not found",
                        },
                    }
                },
            },
            500: {
                "description": "Internal Server Error",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Error"},
                        "example": {
                            "type": "https://tools.ietf.org/html/rfc7807",
                            "title": "Internal Server Error",
                            "status": 500,
                            "detail": "The server encountered an unexpected condition that prevented it from fulfilling the request",
                        },
                    }
                },
            },
            503: {
                "description": "Service Unavailable",
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/Error"},
                        "example": {
                            "type": "https://tools.ietf.org/html/rfc7807",
                            "title": "Service Unavailable",
                            "status": 503,
                            "detail": "The server is currently unable to handle the request due to temporary overloading or maintenance",
                        },
                    }
                },
            },
        }

        if "create" in operations:
            op = operations["create"]["operation"]

            @router.post(
                collection_path,
                summary=op.get("summary", f"Create {resource_name}"),
                description=op.get("description", ""),
                response_model=model,
                status_code=201,
                operation_id=op.get("operationId", f"create_{resource_name}"),
                responses={
                    201: {"description": "Created"},
                    **error_responses,
                    422: {
                        "description": "Validation Error",
                        "content": {
                            "application/problem+json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ValidationError"
                                }
                            }
                        },
                    },
                },
            )
            async def create_resource(data: model, service=Depends(service_dependency)):
                return await service.create(data.model_dump())

        if "read" in operations:
            op = operations["read"]["operation"]

            @router.get(
                item_path,
                summary=op.get("summary", f"Get {resource_name} by ID"),
                description=op.get("description", ""),
                response_model=model,
                operation_id=op.get("operationId", f"get_{resource_name}"),
                responses={200: {"description": "Success"}, **error_responses},
            )
            async def read_resource(id: str, service=Depends(service_dependency)):
                return await service.read(id)

        if "update" in operations:
            op = operations["update"]["operation"]

            @router.put(
                item_path,
                summary=op.get("summary", f"Update {resource_name}"),
                description=op.get("description", ""),
                response_model=model,
                operation_id=op.get("operationId", f"update_{resource_name}"),
                responses={
                    200: {"description": "Success"},
                    **error_responses,
                    422: {
                        "description": "Validation Error",
                        "content": {
                            "application/problem+json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ValidationError"
                                }
                            }
                        },
                    },
                },
            )
            async def update_resource(
                id: str, data: model, service=Depends(service_dependency)
            ):
                return await service.update(id, data.model_dump(), partial=False)

        if "update_partial" in operations:
            op = operations["update_partial"]["operation"]

            @router.patch(
                item_path,
                summary=op.get("summary", f"Partially update {resource_name}"),
                description=op.get("description", ""),
                response_model=model,
                operation_id=op.get("operationId", f"patch_{resource_name}"),
                responses={
                    200: {"description": "Success"},
                    **error_responses,
                    422: {
                        "description": "Validation Error",
                        "content": {
                            "application/problem+json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ValidationError"
                                }
                            }
                        },
                    },
                },
            )
            async def patch_resource(
                id: str, data: Dict[str, Any], service=Depends(service_dependency)
            ):
                return await service.update(id, data, partial=True)

        if "delete" in operations:
            op = operations["delete"]["operation"]

            @router.delete(
                item_path,
                summary=op.get("summary", f"Delete {resource_name}"),
                description=op.get("description", ""),
                status_code=204,
                operation_id=op.get("operationId", f"delete_{resource_name}"),
                responses={204: {"description": "No Content"}, **error_responses},
            )
            async def delete_resource(id: str, service=Depends(service_dependency)):
                await service.delete(id)
                return None

        if "list" in operations:
            op = operations["list"]["operation"]

            @router.get(
                collection_path,
                summary=op.get("summary", f"List {resource_name}"),
                description=op.get("description", ""),
                response_model=List[model],
                operation_id=op.get("operationId", f"list_{resource_name}"),
                responses={200: {"description": "Success"}, **error_responses},
            )
            async def list_resources(
                limit: int = 100, offset: int = 0, service=Depends(service_dependency)
            ):
                return await service.list(limit=limit, offset=offset)

        return router


def create_liveapi_app(*spec_paths: str) -> FastAPI:
    """Convenience function to create a LiveAPI app from one or more specs."""
    router = LiveAPIRouter()
    return router.create_app_from_specs(*spec_paths)


def add_error_schemas_to_app(app: FastAPI):
    """Add standard error schemas to a FastAPI app's OpenAPI schema.

    This function should be called after creating a FastAPI app and including
    LiveAPIRouter routers, but before serving the app, to ensure that all
    error schemas referenced in the router endpoints are properly defined.
    """

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        from fastapi.openapi.utils import get_openapi

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Add components section if not present
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}

        # Add Error schema if not already present
        if "Error" not in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["Error"] = {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "title": {"type": "string"},
                    "status": {"type": "integer"},
                    "detail": {"type": "string"},
                },
                "required": ["type", "title", "status", "detail"],
            }

        # Add/update ValidationError schema to ensure correct RFC 7807 format
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
            "example": {
                "errors": [
                    {
                        "title": "Unprocessable Entity",
                        "detail": "String should have at least 2 characters",
                        "status": "422",
                        "source": {"pointer": "/data/attributes/name"},
                    }
                ]
            },
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

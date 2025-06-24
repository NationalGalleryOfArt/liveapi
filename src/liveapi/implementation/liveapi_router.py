"""LiveAPI router that maps CRUD+ resources to standard handlers."""

from typing import Dict, Any, List, Type, Union
from pathlib import Path
from fastapi import APIRouter, FastAPI, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session
from .liveapi_parser import LiveAPIParser
from .default_resource_service import DefaultResourceService
from .exceptions import BusinessException
from .database import get_db_session


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
        self.handlers: Dict[str, Union[DefaultResourceService, Any]] = {}
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

    def _create_service_dependency(self, model: Type[BaseModel], resource_name: str):
        """Create a dependency factory for the appropriate service."""
        if self.backend_type == "sqlmodel":
            try:
                from .sql_model_resource_service import SQLModelResourceService

                def get_sql_service(session: Session = Depends(get_db_session)):
                    return SQLModelResourceService(
                        model=model, resource_name=resource_name, session=session
                    )

                return get_sql_service
            except ImportError:
                print("⚠️ SQLModel backend not available, falling back to default")
                # Create a singleton service instance for default backend
                if resource_name not in self.handlers:
                    self.handlers[resource_name] = DefaultResourceService(
                        model=model, resource_name=resource_name
                    )

                def get_default_service():
                    return self.handlers[resource_name]

                return get_default_service
        else:
            # Create a singleton service instance for default backend
            if resource_name not in self.handlers:
                self.handlers[resource_name] = DefaultResourceService(
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
        """Create a router for a CRUD+ resource."""
        router = APIRouter()
        service_dependency = self._create_service_dependency(model, resource_name)

        collection_path = resource_info["paths"]["collection"] or f"/{resource_name}"
        item_path = resource_info["paths"]["item"] or f"/{resource_name}/{{id}}"

        operations = resource_info["operations"]

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
            )
            async def list_resources(
                limit: int = 100, offset: int = 0, service=Depends(service_dependency)
            ):
                return await service.list(limit=limit, offset=offset)

        return router


def create_liveapi_app(spec_path: str) -> FastAPI:
    """Convenience function to create a LiveAPI app from a spec."""
    router = LiveAPIRouter()
    return router.create_app_from_spec(spec_path)

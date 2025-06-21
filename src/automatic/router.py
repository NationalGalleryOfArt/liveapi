"""Dynamic FastAPI route generator."""

from typing import Dict, Any, List, Callable, Optional
from fastapi import Request, Depends, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, create_model
from .parser import OpenAPIParser
from .response_transformer import ResponseTransformer
from .request_processor import RequestProcessor


class RouteGenerator:
    """Generates FastAPI routes from OpenAPI specifications."""

    def __init__(
        self,
        implementation: Any,
        path_prefix: str = "",
        auth_dependency: Optional[Callable] = None,
    ):
        self.implementation = implementation
        self.path_prefix = path_prefix.rstrip("/")  # Remove trailing slash
        self.routes: List[Dict[str, Any]] = []
        self.response_transformer = ResponseTransformer()
        self.auth_dependency = auth_dependency
        self.request_processor = RequestProcessor(implementation, self.response_transformer)

    def generate_routes(self, parser: OpenAPIParser) -> List[APIRoute]:
        """Generate FastAPI routes from parsed OpenAPI spec."""
        self.routes = parser.get_routes()
        api_routes = []

        # Update response transformer with OpenAPI spec for validation
        self.response_transformer.update_spec(parser.spec)

        # Extract version from filename
        file_version = parser.extract_version_from_filename()

        for route_info in self.routes:
            # Extract version from operationId or use file version
            operation_version = parser.extract_version_from_operation_id(
                route_info["operation_id"]
            )
            version = operation_version if operation_version > 1 else file_version

            # Add version info to route_info
            route_info["version"] = version

            handler = self._create_route_handler(route_info)

            # Convert OpenAPI path to FastAPI path format and apply prefix
            fastapi_path = self._convert_path_format(route_info["path"])
            if self.path_prefix:
                fastapi_path = self.path_prefix + fastapi_path

            api_route = APIRoute(
                path=fastapi_path,
                endpoint=handler,
                methods=[route_info["method"]],
                name=route_info["operation_id"],
                summary=route_info["summary"],
                description=route_info["description"],
            )

            api_routes.append(api_route)

        return api_routes

    def _create_route_handler(self, route_info: Dict[str, Any]) -> Callable:
        """Create a FastAPI route handler for the given route info."""
        operation_id = route_info["operation_id"]
        version = route_info.get("version", 1)

        # Check if implementation has the required method
        if not hasattr(self.implementation, operation_id):
            raise AttributeError(f"Implementation missing method: {operation_id}")

        # Create dynamic request model if needed
        request_model = self._create_request_model(route_info)

        # Create unified handler that works with or without auth
        async def route_handler(
            request: Request,
            response: Response,
            auth_info: Optional[Dict[str, Any]] = Depends(self.auth_dependency()) if self.auth_dependency else None,
        ):
            try:
                # Prepare data for implementation method
                data = await self.request_processor.prepare_request_data(
                    request, route_info, request_model
                )

                # Add auth info to data if present
                if auth_info:
                    data["auth"] = auth_info

                # Try CRUD delegation first
                result = self.request_processor.handle_crud_delegation(
                    operation_id, data, auth_info
                )
                
                # If not a CRUD operation, call the method directly
                if result is None:
                    result = self.request_processor.call_method_with_version(
                        operation_id, data, version
                    )

                # Handle response transformation
                return self.request_processor.handle_response(result, route_info, response)

            except Exception as e:
                return self.request_processor.handle_exceptions(e, response)

        return route_handler

    def _create_request_model(self, route_info: Dict[str, Any]) -> Optional[BaseModel]:
        """Create a Pydantic model for request validation."""
        request_body = route_info.get("request_body")
        if not request_body:
            return None

        # Simple schema to Pydantic field conversion
        fields = {}
        properties = request_body.get("properties", {})
        required = request_body.get("required", [])

        for field_name, field_schema in properties.items():
            field_type = self._schema_to_python_type(field_schema)
            default_value = ... if field_name in required else None
            fields[field_name] = (field_type, default_value)

        if fields:
            return create_model("RequestModel", **fields)

        return None

    def _schema_to_python_type(self, schema: Dict[str, Any]):
        """Convert OpenAPI schema type to Python type."""
        schema_type = schema.get("type", "string")

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        return type_mapping.get(schema_type, str)

    def _convert_path_format(self, openapi_path: str) -> str:
        """Convert OpenAPI path format to FastAPI path format."""
        # OpenAPI uses {param} format, FastAPI also uses {param} format
        # So no conversion needed for basic cases
        return openapi_path

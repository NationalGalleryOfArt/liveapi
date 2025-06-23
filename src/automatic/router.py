"""Dynamic FastAPI route generator."""

import inspect
from typing import Dict, Any, List, Callable, Optional, Type
from fastapi import Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, create_model, Field, RootModel
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
        self.request_processor = RequestProcessor(
            implementation, self.response_transformer
        )

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

            # Create response models for this route
            response_models = self._create_response_models(route_info)

            # Get the success response model (2xx)
            success_response_model = None
            for status_code, model in response_models.items():
                if status_code.startswith("2"):
                    success_response_model = model
                    break

            # Create the API route with proper response model
            api_route = APIRoute(
                path=fastapi_path,
                endpoint=handler,
                methods=[route_info["method"]],
                name=route_info["operation_id"],
                summary=route_info["summary"],
                description=route_info["description"],
                response_model=success_response_model,
                responses={
                    status: {"model": model}
                    for status, model in response_models.items()
                    if not status.startswith("2")  # Non-success responses
                },
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

        # Extract parameters for FastAPI route
        parameters = route_info.get("parameters", [])
        path_params = [p for p in parameters if p.get("in") == "path"]
        query_params = [p for p in parameters if p.get("in") == "query"]

        # Create response models for this route
        response_models = self._create_response_models(route_info)

        # Get the success response model (2xx)
        success_response_model = None
        for status_code, model in response_models.items():
            if status_code.startswith("2"):
                success_response_model = model
                break

        # Create the parameter signature for the route handler
        # This will be used to dynamically create the handler function with the right parameters
        param_signature = {}

        # Add path parameters to the signature
        for param in path_params:
            param_name = param.get("name")
            param_type = self._schema_to_python_type(param.get("schema", {}))
            param_signature[param_name] = (param_type, ...)

        # Add query parameters to the signature
        for param in query_params:
            param_name = param.get("name")
            param_type = self._schema_to_python_type(param.get("schema", {}))
            param_required = param.get("required", False)
            if param_required:
                param_signature[param_name] = (param_type, ...)
            else:
                param_signature[param_name] = (Optional[param_type], None)

        # Add request body if needed
        if request_model:
            param_signature["body"] = (request_model, ...)

        # Create unified handler that works with or without auth
        # Define the handler with proper type annotations for parameters
        async def route_handler(
            request: Request,
            response: Response,
            # Add explicit parameters for path and query params
            # These will be populated by FastAPI based on the path and query parameters
            # defined in the OpenAPI spec
            **path_query_params,  # This will capture all path and query parameters
        ):
            try:
                # Prepare data for implementation method
                data = await self.request_processor.prepare_request_data(
                    request, route_info, request_model
                )

                # Add path and query parameters to data
                data.update(path_query_params)

                # Add auth info to data if present
                auth_info = None
                if self.auth_dependency:
                    auth_info = await self.auth_dependency()(request)
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
                return self.request_processor.handle_response(
                    result, route_info, response
                )

            except Exception as e:
                return self.request_processor.handle_exceptions(e, response)

        # Set the handler signature to properly document parameters in OpenAPI
        route_handler.__signature__ = self._create_handler_signature(
            route_handler, path_params, query_params, request_model
        )

        # Set response model annotation for better OpenAPI docs
        if success_response_model:
            # Use the first 2xx response model as the return annotation
            route_handler.__annotations__["return"] = success_response_model

        return route_handler

    def _create_request_model(
        self, route_info: Dict[str, Any]
    ) -> Optional[Type[BaseModel]]:
        """Create a Pydantic model for request validation."""
        request_body = route_info.get("request_body")
        if not request_body:
            return None

        # Get operation ID for naming the model
        operation_id = route_info.get("operation_id", "Request")
        model_name = f"{operation_id.capitalize()}Model"

        # Simple schema to Pydantic field conversion
        fields = {}
        properties = request_body.get("properties", {})
        required = request_body.get("required", [])

        for field_name, field_schema in properties.items():
            field_type = self._schema_to_python_type(field_schema)
            description = field_schema.get("description", "")

            # Use Field for better documentation
            if field_name in required:
                fields[field_name] = (field_type, Field(..., description=description))
            else:
                fields[field_name] = (field_type, Field(None, description=description))

        if fields:
            return create_model(model_name, **fields)

        return None

    def _create_response_models(
        self, route_info: Dict[str, Any]
    ) -> Dict[str, Type[BaseModel]]:
        """Create Pydantic models for response schemas."""
        responses = route_info.get("responses", {})
        operation_id = route_info.get("operation_id", "Response")

        response_models = {}

        for status_code, response_info in responses.items():
            if not isinstance(response_info, dict):
                continue

            # Get content from response
            content = response_info.get("content", {})

            # Try to get JSON schema first
            schema = None
            if "application/json" in content:
                schema = content["application/json"].get("schema")

            # If no JSON schema, try any other content type
            if not schema and content:
                first_content = next(iter(content.values()))
                schema = first_content.get("schema")

            # If we have a schema, create a model
            if schema:
                model_name = f"{operation_id.capitalize()}{status_code}Response"

                # Handle reference schemas
                if "$ref" in schema:
                    # For now, create a simple model with the reference name
                    ref_parts = schema["$ref"].split("/")
                    ref_name = ref_parts[-1]

                    # Create a RootModel for the reference
                    RefModel = RootModel[Dict[str, Any]]
                    RefModel.__doc__ = f"Reference to {ref_name}"
                    response_models[status_code] = RefModel
                    continue

                # Handle array schemas
                if schema.get("type") == "array" and "items" in schema:
                    items_schema = schema["items"]
                    if "$ref" in items_schema:
                        # Reference to another schema
                        ref_parts = items_schema["$ref"].split("/")
                        ref_name = ref_parts[-1]

                        # Create a RootModel for the array of references
                        ArrayRefModel = RootModel[List[Dict[str, Any]]]
                        ArrayRefModel.__doc__ = f"Array of {ref_name}"
                        response_models[status_code] = ArrayRefModel
                    else:
                        # Simple array type
                        item_type = self._schema_to_python_type(items_schema)

                        # Create a RootModel for the array
                        ArrayModel = RootModel[List[item_type]]
                        ArrayModel.__doc__ = "Array response"
                        response_models[status_code] = ArrayModel
                    continue

                # Handle object schemas
                if schema.get("type") == "object" or "properties" in schema:
                    fields = {}
                    properties = schema.get("properties", {})
                    required = schema.get("required", [])

                    for field_name, field_schema in properties.items():
                        field_type = self._schema_to_python_type(field_schema)
                        description = field_schema.get("description", "")

                        if field_name in required:
                            fields[field_name] = (
                                field_type,
                                Field(..., description=description),
                            )
                        else:
                            fields[field_name] = (
                                field_type,
                                Field(None, description=description),
                            )

                    if fields:
                        response_models[status_code] = create_model(
                            model_name, **fields
                        )
                    else:
                        # Empty object
                        EmptyModel = RootModel[Dict[str, Any]]
                        EmptyModel.__doc__ = "Empty object"
                        response_models[status_code] = EmptyModel
                    continue

                # Handle primitive types
                primitive_type = self._schema_to_python_type(schema)

                # Create a RootModel for the primitive type
                PrimitiveModel = RootModel[primitive_type]
                PrimitiveModel.__doc__ = response_info.get("description", "")
                response_models[status_code] = PrimitiveModel
            else:
                # No schema, create a generic model
                GenericModel = RootModel[Dict[str, Any]]
                GenericModel.__doc__ = response_info.get("description", "")
                response_models[status_code] = GenericModel

        return response_models

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

    def _create_handler_signature(
        self,
        handler: Callable,
        path_params: List[Dict[str, Any]],
        query_params: List[Dict[str, Any]],
        request_model: Optional[BaseModel],
    ) -> inspect.Signature:
        """Create a proper signature for the handler function to expose parameters in OpenAPI docs."""
        from inspect import Parameter

        # Start with the original parameters (request, response)
        original_sig = inspect.signature(handler)
        original_params = []

        # Only include request and response parameters, not path_query_params
        for name, param in original_sig.parameters.items():
            if name in ["request", "response"]:
                original_params.append(param)

        # Separate required and optional parameters
        required_params = []
        optional_params = []

        # Process original parameters
        for param in original_params:
            if param.default is Parameter.empty:
                required_params.append(param)
            else:
                optional_params.append(param)

        # Add path parameters (always required)
        for param in path_params:
            param_name = param.get("name")
            param_type = self._schema_to_python_type(param.get("schema", {}))
            required_params.append(
                Parameter(
                    name=param_name,
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=param_type,
                    default=Parameter.empty,
                )
            )

        # Add required query parameters
        for param in query_params:
            param_name = param.get("name")
            param_type = self._schema_to_python_type(param.get("schema", {}))
            param_required = param.get("required", False)

            if param_required:
                required_params.append(
                    Parameter(
                        name=param_name,
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=param_type,
                        default=Parameter.empty,
                    )
                )
            else:
                optional_params.append(
                    Parameter(
                        name=param_name,
                        kind=Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=Optional[param_type],
                        default=None,
                    )
                )

        # Add request body if needed (always required)
        if request_model:
            required_params.append(
                Parameter(
                    name="body",
                    kind=Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=request_model,
                    default=Parameter.empty,
                )
            )

        # Add the path_query_params parameter last (it must be last as it's a variadic keyword parameter)
        path_query_params_param = Parameter(
            name="path_query_params",
            kind=Parameter.VAR_KEYWORD,
            annotation=Dict[str, Any],
            default=Parameter.empty,
        )

        # Combine parameters in the correct order: required first, then optional, then variadic
        parameters = required_params + optional_params + [path_query_params_param]

        return inspect.Signature(
            parameters=parameters, return_annotation=original_sig.return_annotation
        )

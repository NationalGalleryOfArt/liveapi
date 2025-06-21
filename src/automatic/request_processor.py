"""Request processing logic extracted from RouteGenerator."""

from typing import Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from pydantic import BaseModel, ValidationError
import inspect
from .response_transformer import ResponseTransformer
from .exceptions import BusinessException


class RequestProcessor:
    """Handles request processing and response transformation for route handlers."""

    def __init__(self, implementation: Any, response_transformer: ResponseTransformer):
        self.implementation = implementation
        self.response_transformer = response_transformer

    async def prepare_request_data(
        self,
        request: Request,
        route_info: Dict[str, Any],
        request_model: Optional[BaseModel],
    ) -> Dict[str, Any]:
        """Prepare request data for implementation method."""
        data = {}

        # Add path parameters
        data.update(request.path_params)

        # Add query parameters
        data.update(dict(request.query_params))

        # Add request body if present
        if request_model and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                validated_data = request_model(**body)
                data.update(validated_data.model_dump())
            except Exception:
                # If JSON parsing fails, try to get raw body
                body = await request.body()
                if body:
                    data["body"] = body.decode("utf-8")

        return data

    def handle_crud_delegation(
        self, operation_id: str, data: Dict[str, Any], auth_info: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Handle CRUD operation delegation to base class methods."""
        crud_methods = {"index", "show", "create", "update", "destroy"}
        
        if operation_id not in crud_methods:
            return None  # Not a CRUD operation
            
        auth = auth_info

        if operation_id == "index":
            filters = {k: v for k, v in data.items() if k not in ["auth", "body"]}
            return getattr(self.implementation, "index")(filters, auth)
        
        elif operation_id == "show":
            resource_id = data.get("id") or next(
                (v for k, v in data.items() if k.endswith("id")), None
            )
            if not resource_id:
                raise ValidationError("Resource ID is required")
            return getattr(self.implementation, "show")(resource_id, auth)
        
        elif operation_id == "create":
            body = data.get("body", data)
            return getattr(self.implementation, "create")(body, auth)
        
        elif operation_id == "update":
            resource_id = data.get("id") or next(
                (v for k, v in data.items() if k.endswith("id")), None
            )
            if not resource_id:
                raise ValidationError("Resource ID is required")
            body = data.get("body", data)
            return getattr(self.implementation, "update")(resource_id, body, auth)
        
        elif operation_id == "destroy":
            resource_id = data.get("id") or next(
                (v for k, v in data.items() if k.endswith("id")), None
            )
            if not resource_id:
                raise ValidationError("Resource ID is required")
            return getattr(self.implementation, "destroy")(resource_id, auth)

    def call_method_with_version(
        self, method_name: str, data: Dict[str, Any], version: int
    ) -> Any:
        """Call a method with version parameter if it accepts it."""
        if not hasattr(self.implementation, method_name):
            raise AttributeError(f"Implementation missing method: {method_name}")

        method = getattr(self.implementation, method_name)

        if self._method_accepts_version_parameter(method_name):
            return method(data, version=version)
        else:
            return method(data)

    def _method_accepts_version_parameter(self, method_name: str) -> bool:
        """Check if a method accepts a version parameter."""
        if not hasattr(self.implementation, method_name):
            return False

        method = getattr(self.implementation, method_name)
        sig = inspect.signature(method)
        return "version" in sig.parameters

    def handle_response(
        self, result: Any, route_info: Dict[str, Any], response: Response
    ) -> Any:
        """Handle response transformation and status code setting."""
        operation_id = route_info.get("operation_id")
        version = route_info.get("version", 1)
        
        if isinstance(result, tuple) and len(result) == 2:
            response_data, status_code = result
            response.status_code = status_code

            # Transform response using RFC 9457 for errors and validation for success
            transformed_data = self.response_transformer.transform_response(
                response_data, status_code, operation_id, version
            )
            return transformed_data
        else:
            # Auto-infer status code from HTTP method for non-CRUD operations
            inferred_status = self._infer_status_code(route_info["method"])
            response.status_code = inferred_status
            
            # Apply validation and conversion for successful responses
            transformed_data = self.response_transformer.transform_response(
                result, inferred_status, operation_id, version
            )
            return transformed_data

    def handle_exceptions(self, e: Exception, response: Response) -> Dict[str, Any]:
        """Handle exceptions and convert them to appropriate HTTP responses."""
        if isinstance(e, ValidationError):
            raise HTTPException(status_code=422, detail=e.errors())
        
        elif isinstance(e, BusinessException):
            # Business exceptions get converted to proper HTTP responses
            response.status_code = e.status_code
            return e.to_response()
        
        elif isinstance(e, NotImplementedError):
            # Map NotImplementedError to HTTP 501 Not Implemented
            response.status_code = 501
            return {
                "type": "/errors/not_implemented",
                "title": "Not Implemented",
                "status": 501,
                "detail": str(e) or "This operation is not implemented."
            }
        
        else:
            # Unexpected errors become 500s with RFC 9457 format
            response.status_code = 500
            return {
                "type": "/errors/internal_server_error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": (
                    str(e)
                    if isinstance(e, (ValueError, TypeError, KeyError))
                    else "An unexpected error occurred"
                ),
            }

    def _infer_status_code(self, http_method: str) -> int:
        """Infer appropriate HTTP status code from HTTP method."""
        method_status_map = {
            "GET": 200,      # OK
            "POST": 201,     # Created
            "PUT": 200,      # OK (full replacement)
            "PATCH": 200,    # OK (partial update)
            "DELETE": 204,   # No Content
            "HEAD": 200,     # OK
            "OPTIONS": 200,  # OK
        }

        return method_status_map.get(http_method.upper(), 200)

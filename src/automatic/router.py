"""Dynamic FastAPI route generator."""

from typing import Dict, Any, List, Callable, Optional, Union
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.routing import APIRoute
from pydantic import BaseModel, create_model, ValidationError
import inspect
from .parser import OpenAPIParser


class RouteGenerator:
    """Generates FastAPI routes from OpenAPI specifications."""
    
    def __init__(self, implementation: Any, path_prefix: str = ""):
        self.implementation = implementation
        self.path_prefix = path_prefix.rstrip('/')  # Remove trailing slash
        self.routes: List[Dict[str, Any]] = []
    
    def generate_routes(self, parser: OpenAPIParser) -> List[APIRoute]:
        """Generate FastAPI routes from parsed OpenAPI spec."""
        self.routes = parser.get_routes()
        api_routes = []
        
        for route_info in self.routes:
            handler = self._create_route_handler(route_info)
            
            # Convert OpenAPI path to FastAPI path format and apply prefix
            fastapi_path = self._convert_path_format(route_info['path'])
            if self.path_prefix:
                fastapi_path = self.path_prefix + fastapi_path
            
            api_route = APIRoute(
                path=fastapi_path,
                endpoint=handler,
                methods=[route_info['method']],
                name=route_info['operation_id'],
                summary=route_info['summary'],
                description=route_info['description']
            )
            
            api_routes.append(api_route)
        
        return api_routes
    
    def _create_route_handler(self, route_info: Dict[str, Any]) -> Callable:
        """Create a FastAPI route handler for the given route info."""
        operation_id = route_info['operation_id']
        
        # Check if implementation has the required method
        if not hasattr(self.implementation, operation_id):
            raise AttributeError(f"Implementation missing method: {operation_id}")
        
        impl_method = getattr(self.implementation, operation_id)
        
        # Create dynamic request model if needed
        request_model = self._create_request_model(route_info)
        
        async def route_handler(request: Request):
            try:
                # Prepare data for implementation method
                data = await self._prepare_request_data(request, route_info, request_model)
                
                # Call implementation method
                result = impl_method(data)
                
                # Handle response
                if isinstance(result, tuple) and len(result) == 2:
                    response_data, status_code = result
                    return response_data
                else:
                    return result
                    
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=e.errors())
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        return route_handler
    
    def _create_request_model(self, route_info: Dict[str, Any]) -> Optional[BaseModel]:
        """Create a Pydantic model for request validation."""
        request_body = route_info.get('request_body')
        if not request_body:
            return None
        
        # Simple schema to Pydantic field conversion
        fields = {}
        properties = request_body.get('properties', {})
        required = request_body.get('required', [])
        
        for field_name, field_schema in properties.items():
            field_type = self._schema_to_python_type(field_schema)
            default_value = ... if field_name in required else None
            fields[field_name] = (field_type, default_value)
        
        if fields:
            return create_model('RequestModel', **fields)
        
        return None
    
    def _schema_to_python_type(self, schema: Dict[str, Any]):
        """Convert OpenAPI schema type to Python type."""
        schema_type = schema.get('type', 'string')
        
        type_mapping = {
            'string': str,
            'integer': int,
            'number': float,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        return type_mapping.get(schema_type, str)
    
    def _convert_path_format(self, openapi_path: str) -> str:
        """Convert OpenAPI path format to FastAPI path format."""
        # OpenAPI uses {param} format, FastAPI also uses {param} format
        # So no conversion needed for basic cases
        return openapi_path
    
    async def _prepare_request_data(self, request: Request, route_info: Dict[str, Any], request_model: Optional[BaseModel]) -> Dict[str, Any]:
        """Prepare request data for implementation method."""
        data = {}
        
        # Add path parameters
        data.update(request.path_params)
        
        # Add query parameters
        data.update(dict(request.query_params))
        
        # Add request body if present
        if request_model and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.json()
                validated_data = request_model(**body)
                data.update(validated_data.dict())
            except Exception:
                # If JSON parsing fails, try to get raw body
                body = await request.body()
                if body:
                    data['body'] = body.decode('utf-8')
        
        return data
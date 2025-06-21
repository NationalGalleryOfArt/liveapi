"""Response validation and conversion layer for OpenAPI schema compliance."""

import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Validates and converts response data to match OpenAPI schema definitions."""

    def __init__(self, spec: Optional[Dict[str, Any]] = None):
        self.spec = spec
        self.response_schemas = {}
        self._extract_response_schemas()

    def _extract_response_schemas(self):
        """Extract response schemas from OpenAPI spec for validation."""
        if not self.spec:
            return

        paths = self.spec.get("paths", {})
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch", "head", "options"]:
                operation = path_item.get(method)
                if not operation:
                    continue

                operation_id = operation.get("operationId")
                if not operation_id:
                    continue

                # Extract response schemas for successful responses
                responses = operation.get("responses", {})
                success_responses = {
                    code: resp for code, resp in responses.items()
                    if code.startswith("2") or code == "default"
                }

                if success_responses:
                    self.response_schemas[operation_id] = success_responses

    def validate_and_convert(
        self,
        data: Any,
        operation_id: str,
        status_code: int = 200,
        version: int = 1
    ) -> Any:
        """
        Validate and convert response data to match OpenAPI schema.
        
        Args:
            data: Response data to validate and convert
            operation_id: OpenAPI operation ID
            status_code: HTTP status code
            version: API version for version-aware validation
            
        Returns:
            Validated and converted response data
        """
        try:
            # Skip validation for error responses (handled by ResponseTransformer)
            if status_code >= 400:
                return data

            # Get response schema for this operation
            schema = self._get_response_schema(operation_id, status_code)
            if not schema:
                logger.debug(f"No schema found for {operation_id}, returning data as-is")
                return data

            # Apply conversions and validation
            converted_data = self._convert_and_validate(data, schema, version)
            
            logger.debug(f"Successfully validated response for {operation_id}")
            return converted_data

        except Exception as e:
            logger.warning(f"Response validation failed for {operation_id}: {e}")
            # Return original data on validation failure to avoid breaking API
            return data

    def _get_response_schema(self, operation_id: str, status_code: int) -> Optional[Dict]:
        """Get response schema for operation and status code."""
        operation_schemas = self.response_schemas.get(operation_id, {})
        
        # Try exact status code match first
        status_str = str(status_code)
        if status_str in operation_schemas:
            return self._extract_content_schema(operation_schemas[status_str])
        
        # Try default response
        if "default" in operation_schemas:
            return self._extract_content_schema(operation_schemas["default"])
        
        # Try 2xx pattern
        if status_str.startswith("2") and "2XX" in operation_schemas:
            return self._extract_content_schema(operation_schemas["2XX"])
            
        return None

    def _extract_content_schema(self, response_spec: Dict) -> Optional[Dict]:
        """Extract schema from response content specification."""
        content = response_spec.get("content", {})
        
        # Try JSON content type first
        json_content = content.get("application/json", {})
        if json_content:
            return json_content.get("schema")
        
        # Try any content type
        for content_type, content_spec in content.items():
            schema = content_spec.get("schema")
            if schema:
                return schema
                
        return None

    def _convert_and_validate(self, data: Any, schema: Dict, version: int) -> Any:
        """Convert and validate data against schema."""
        if not schema:
            return data

        schema_type = schema.get("type")
        
        if schema_type == "object":
            return self._convert_object(data, schema, version)
        elif schema_type == "array":
            return self._convert_array(data, schema, version)
        else:
            return self._convert_primitive(data, schema)

    def _convert_object(self, data: Any, schema: Dict, version: int) -> Dict:
        """Convert and validate object data."""
        if not isinstance(data, dict):
            logger.warning(f"Expected object, got {type(data)}")
            return data

        result = {}
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        # Process existing fields
        for key, value in data.items():
            if key in properties:
                field_schema = properties[key]
                result[key] = self._convert_and_validate(value, field_schema, version)
            else:
                # Include unknown fields (additionalProperties behavior)
                result[key] = self._sanitize_field(key, value, version)

        # Add missing required fields with defaults
        for field_name in required_fields:
            if field_name not in result:
                field_schema = properties.get(field_name, {})
                default_value = self._get_default_value(field_schema)
                if default_value is not None:
                    result[field_name] = default_value
                    logger.debug(f"Added missing required field '{field_name}' with default value")

        return result

    def _convert_array(self, data: Any, schema: Dict, version: int) -> List:
        """Convert and validate array data."""
        if not isinstance(data, (list, tuple)):
            logger.warning(f"Expected array, got {type(data)}")
            return data if isinstance(data, list) else [data]

        items_schema = schema.get("items", {})
        return [self._convert_and_validate(item, items_schema, version) for item in data]

    def _convert_primitive(self, data: Any, schema: Dict) -> Any:
        """Convert primitive data types."""
        schema_type = schema.get("type")
        schema_format = schema.get("format")

        try:
            if schema_type == "string":
                return self._convert_to_string(data, schema_format)
            elif schema_type == "integer":
                return self._convert_to_integer(data)
            elif schema_type == "number":
                return self._convert_to_number(data)
            elif schema_type == "boolean":
                return self._convert_to_boolean(data)
            else:
                return data
        except (ValueError, TypeError) as e:
            logger.warning(f"Type conversion failed: {e}")
            return data

    def _convert_to_string(self, data: Any, format_type: Optional[str] = None) -> str:
        """Convert data to string with format handling."""
        if isinstance(data, str):
            return data

        if format_type == "date-time" and isinstance(data, datetime):
            return data.isoformat()
        elif format_type == "date" and isinstance(data, datetime):
            return data.date().isoformat()

        return str(data)

    def _convert_to_integer(self, data: Any) -> int:
        """Convert data to integer."""
        if isinstance(data, int):
            return data
        if isinstance(data, float) and data.is_integer():
            return int(data)
        if isinstance(data, str) and data.isdigit():
            return int(data)
        
        return int(data)  # Let it raise ValueError if conversion fails

    def _convert_to_number(self, data: Any) -> Union[int, float]:
        """Convert data to number (int or float)."""
        if isinstance(data, (int, float)):
            return data
        if isinstance(data, str):
            try:
                # Try int first, then float
                if '.' not in data:
                    return int(data)
                return float(data)
            except ValueError:
                raise ValueError(f"Cannot convert '{data}' to number")
        
        return float(data)

    def _convert_to_boolean(self, data: Any) -> bool:
        """Convert data to boolean."""
        if isinstance(data, bool):
            return data
        if isinstance(data, str):
            return data.lower() in ("true", "1", "yes", "on")
        if isinstance(data, (int, float)):
            return bool(data)
        
        return bool(data)

    def _sanitize_field(self, field_name: str, value: Any, version: int) -> Any:
        """Sanitize field values based on naming patterns and version."""
        # Remove internal fields
        if field_name.startswith("_") or field_name.startswith("internal_"):
            return None

        # Remove sensitive fields
        sensitive_patterns = ["password", "secret", "token", "key", "hash"]
        if any(pattern in field_name.lower() for pattern in sensitive_patterns):
            return "[REDACTED]"

        # Version-specific field handling
        if version >= 2:
            # In v2+, ensure datetime fields are ISO formatted
            if "date" in field_name.lower() or "time" in field_name.lower():
                if isinstance(value, datetime):
                    return value.isoformat()

        return value

    def _get_default_value(self, schema: Dict) -> Any:
        """Get default value for schema type."""
        if "default" in schema:
            return schema["default"]

        schema_type = schema.get("type")
        if schema_type == "string":
            return ""
        elif schema_type == "integer":
            return 0
        elif schema_type == "number":
            return 0.0
        elif schema_type == "boolean":
            return False
        elif schema_type == "array":
            return []
        elif schema_type == "object":
            return {}

        return None

    def update_spec(self, spec: Dict[str, Any]):
        """Update the OpenAPI specification and re-extract schemas."""
        self.spec = spec
        self.response_schemas = {}
        self._extract_response_schemas()

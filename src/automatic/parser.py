"""OpenAPI specification parser using prance."""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import prance
import re


class OpenAPIParser:
    """Parses OpenAPI specifications and extracts route information."""

    def __init__(self, spec_path: Union[str, Path]):
        self.spec_path = Path(spec_path)
        self.spec = None

    def load_spec(self):
        """Load OpenAPI specification from file."""
        if not self.spec_path.exists():
            raise FileNotFoundError(f"OpenAPI spec not found: {self.spec_path}")

        # Use prance to parse the OpenAPI spec (fast mode, no validation)
        self.spec = prance.BaseParser(str(self.spec_path), strict=False).specification
        return self.spec

    def get_routes(self) -> List[Dict[str, Any]]:
        """Extract route information from OpenAPI spec."""
        if not self.spec:
            self.load_spec()

        routes = []
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            for method_name in [
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "head",
                "options",
            ]:
                operation = path_item.get(method_name)
                if not operation:
                    continue

                operation_id = operation.get("operationId")
                if not operation_id:
                    raise ValueError(
                        f"Missing operationId for {method_name.upper()} {path}"
                    )

                route_info = {
                    "path": path,
                    "method": method_name.upper(),
                    "operation_id": operation_id,
                    "parameters": self._extract_parameters(operation, path_item),
                    "request_body": self._extract_request_body(operation),
                    "responses": self._extract_responses(operation),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                }

                routes.append(route_info)

        return routes

    def _extract_parameters(self, operation, path_item) -> List[Dict[str, Any]]:
        """Extract parameters from operation and path item."""
        parameters = []

        # Path-level parameters
        path_params = path_item.get("parameters", [])
        parameters.extend(path_params)

        # Operation-level parameters
        op_params = operation.get("parameters", [])
        parameters.extend(op_params)

        return parameters

    def _extract_request_body(self, operation) -> Optional[Dict[str, Any]]:
        """Extract request body schema from operation."""
        request_body = operation.get("requestBody")
        if not request_body:
            return None

        content = request_body.get("content", {})

        # Create a schema object that includes both the original schema and resolved references
        result_schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        # Look for JSON content first
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})

            # If it's a reference, resolve it and merge with result
            if schema and "$ref" in schema:
                ref_schema = self._resolve_schema_reference(schema["$ref"])
                if ref_schema:
                    # Add reference name for better documentation
                    ref_name = self._extract_schema_name_from_ref(schema["$ref"])
                    result_schema["x-schema-name"] = ref_name

                    # Merge properties and required fields
                    result_schema["properties"].update(ref_schema.get("properties", {}))
                    result_schema["required"].extend(ref_schema.get("required", []))

                    # Add any additional schema properties
                    for key, value in ref_schema.items():
                        if (
                            key not in ["properties", "required"]
                            and key not in result_schema
                        ):
                            result_schema[key] = value

                    return result_schema

            # If it's an inline schema, use it directly
            if schema:
                return schema

        # Fallback to first available content type
        if content:
            first_content = next(iter(content.values()))
            schema = first_content.get("schema", {})

            # If it's a reference, resolve it
            if schema and "$ref" in schema:
                ref_schema = self._resolve_schema_reference(schema["$ref"])
                if ref_schema:
                    # Add reference name for better documentation
                    ref_name = self._extract_schema_name_from_ref(schema["$ref"])
                    result_schema["x-schema-name"] = ref_name

                    # Merge properties and required fields
                    result_schema["properties"].update(ref_schema.get("properties", {}))
                    result_schema["required"].extend(ref_schema.get("required", []))

                    # Add any additional schema properties
                    for key, value in ref_schema.items():
                        if (
                            key not in ["properties", "required"]
                            and key not in result_schema
                        ):
                            result_schema[key] = value

                    return result_schema

            # If it's an inline schema, use it directly
            if schema:
                return schema

        return None

    def _extract_responses(self, operation) -> Dict[str, Any]:
        """Extract response schemas from operation."""
        responses = operation.get("responses", {})
        enhanced_responses = {}

        for status_code, response_info in responses.items():
            if not isinstance(response_info, dict):
                enhanced_responses[status_code] = response_info
                continue

            # Create a copy to avoid modifying the original
            enhanced_response = {
                "description": response_info.get("description", ""),
                "content": {},
            }

            # Process content
            content = response_info.get("content", {})
            for content_type, content_info in content.items():
                schema = content_info.get("schema", {})

                # If it's a reference, resolve it
                if schema and "$ref" in schema:
                    ref_schema = self._resolve_schema_reference(schema["$ref"])
                    if ref_schema:
                        # Keep the original reference for model creation
                        enhanced_schema = {
                            "original_ref": schema["$ref"],
                            "ref_name": self._extract_schema_name_from_ref(
                                schema["$ref"]
                            ),
                        }

                        # Add resolved schema properties
                        enhanced_schema.update(ref_schema)

                        # Update the content with enhanced schema
                        enhanced_response["content"][content_type] = {
                            "schema": enhanced_schema
                        }
                        continue

                # Handle array with reference items
                if schema and schema.get("type") == "array" and "items" in schema:
                    items = schema["items"]
                    if "$ref" in items:
                        ref_schema = self._resolve_schema_reference(items["$ref"])
                        if ref_schema:
                            # Keep the original structure but add resolved items
                            enhanced_schema = {
                                "type": "array",
                                "items": {
                                    "original_ref": items["$ref"],
                                    "ref_name": self._extract_schema_name_from_ref(
                                        items["$ref"]
                                    ),
                                },
                            }

                            # Add resolved schema properties to items
                            enhanced_schema["items"].update(ref_schema)

                            # Update the content with enhanced schema
                            enhanced_response["content"][content_type] = {
                                "schema": enhanced_schema
                            }
                            continue

                # If no special handling needed, keep the original
                enhanced_response["content"][content_type] = content_info

            # Add headers if present
            if "headers" in response_info:
                enhanced_response["headers"] = response_info["headers"]

            enhanced_responses[status_code] = enhanced_response

        return enhanced_responses

    def extract_version_from_filename(self) -> int:
        """Extract version number from filename (e.g., users_v2.yaml -> 2)."""
        filename = self.spec_path.name
        match = re.search(r"_v(\d+)\.", filename)
        if match:
            return int(match.group(1))
        return 1  # Default to version 1

    @staticmethod
    def extract_version_from_operation_id(operation_id: str) -> int:
        """Extract version number from operationId (e.g., create_user_v2 -> 2)."""
        match = re.search(r"_v(\d+)$", operation_id)
        if match:
            return int(match.group(1))
        return 1  # Default to version 1

    def _resolve_schema_reference(self, ref: str) -> Optional[Dict[str, Any]]:
        """Resolve a schema reference to the actual schema."""
        if not ref.startswith("#/"):
            return None

        # Parse the reference path
        parts = ref.lstrip("#/").split("/")

        # Navigate through the spec to find the referenced schema
        schema = self.spec
        for part in parts:
            if part not in schema:
                return None
            schema = schema[part]

        # If the resolved schema contains more references, resolve those too
        if isinstance(schema, dict):
            schema = self._resolve_nested_references(schema)

        return schema

    def _resolve_nested_references(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve nested references in a schema."""
        if not isinstance(schema, dict):
            return schema

        # Create a copy to avoid modifying the original
        result = schema.copy()

        # Check for direct reference
        if "$ref" in result:
            ref_schema = self._resolve_schema_reference(result["$ref"])
            if ref_schema:
                # Keep track of the original reference
                ref_name = self._extract_schema_name_from_ref(result["$ref"])
                ref_schema = ref_schema.copy()
                ref_schema["x-schema-name"] = ref_name
                return ref_schema

        # Check for nested references in properties
        if "properties" in result and isinstance(result["properties"], dict):
            for prop_name, prop_schema in result["properties"].items():
                if isinstance(prop_schema, dict) and "$ref" in prop_schema:
                    ref_schema = self._resolve_schema_reference(prop_schema["$ref"])
                    if ref_schema:
                        # Keep track of the original reference
                        ref_name = self._extract_schema_name_from_ref(
                            prop_schema["$ref"]
                        )
                        result["properties"][prop_name] = ref_schema.copy()
                        result["properties"][prop_name]["x-schema-name"] = ref_name

        # Check for nested references in array items
        if "items" in result and isinstance(result["items"], dict):
            if "$ref" in result["items"]:
                ref_schema = self._resolve_schema_reference(result["items"]["$ref"])
                if ref_schema:
                    # Keep track of the original reference
                    ref_name = self._extract_schema_name_from_ref(
                        result["items"]["$ref"]
                    )
                    result["items"] = ref_schema.copy()
                    result["items"]["x-schema-name"] = ref_name

        return result

    def _extract_schema_name_from_ref(self, ref: str) -> str:
        """Extract schema name from a reference string."""
        if not ref.startswith("#/"):
            return "Unknown"

        # Parse the reference path and get the last part
        parts = ref.lstrip("#/").split("/")
        if parts:
            return parts[-1]

        return "Unknown"

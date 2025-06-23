"""OpenAPI specification generator."""

import json
import yaml
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import re

from .interactive import InteractiveGenerator


class SpecGenerator:
    """Generate OpenAPI specifications using structured templates."""

    def __init__(self):
        """Initialize the spec generator."""

        # Initialize interactive generator
        self.interactive = InteractiveGenerator(self)

    def _extract_resource_name(self, endpoint_descriptions: str) -> str:
        """Extract resource name from endpoint descriptions for CRUD APIs.

        Args:
            endpoint_descriptions: User's description of endpoints

        Returns:
            Resource name (e.g., 'locations' from 'full crud api for locations')
        """
        # Try to find resource name after CRUD indicators
        patterns = [
            r"crud\s+api\s+for\s+(\w+)",
            r"full\s+crud\s+(?:api\s+)?for\s+(\w+)",
            r"crud\s+operations\s+for\s+(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, endpoint_descriptions, re.IGNORECASE)
            if match:
                return match.group(1).lower()

        # If no match, look for any plural noun that might be a resource
        words = endpoint_descriptions.split()
        for word in words:
            # Simple heuristic: look for plural words (ending with 's')
            if word.lower().endswith("s") and len(word) > 3:
                # Remove punctuation
                clean_word = re.sub(r"[^\w]", "", word.lower())
                if clean_word:
                    return clean_word

        # Default fallback
        return "resources"

    def _generate_crud_endpoints(self, resource_name: str) -> List[Dict[str, Any]]:
        """Generate standard CRUD endpoints for a resource.

        Args:
            resource_name: Name of the resource (e.g., 'locations')

        Returns:
            List of endpoint dictionaries with standard CRUD operation IDs
        """
        # Get singular form by removing trailing 's' if present
        singular = resource_name[:-1] if resource_name.endswith("s") else resource_name

        return [
            {
                "method": "GET",
                "path": f"/{resource_name}",
                "description": f"List {resource_name}",
                "returns": f"array of {singular.capitalize()} objects",
                "operationId": "index",
            },
            {
                "method": "GET",
                "path": f"/{resource_name}/{{id}}",
                "description": f"Get {singular}",
                "returns": f"{singular.capitalize()} object",
                "operationId": "show",
            },
            {
                "method": "POST",
                "path": f"/{resource_name}",
                "description": f"Create {singular}",
                "returns": f"{singular.capitalize()} object",
                "operationId": "create",
            },
            {
                "method": "PUT",
                "path": f"/{resource_name}/{{id}}",
                "description": f"Update {singular}",
                "returns": f"{singular.capitalize()} object",
                "operationId": "update",
            },
            {
                "method": "DELETE",
                "path": f"/{resource_name}/{{id}}",
                "description": f"Delete {singular}",
                "returns": "empty",
                "operationId": "destroy",
            },
        ]

    def generate_spec_with_json(
        self, api_info: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Generate OpenAPI specification from API information, returning both spec and intermediate JSON.

        Args:
            api_info: Dictionary containing API details

        Returns:
            Tuple of (OpenAPI specification dict, intermediate JSON)
        """
        # Check if this is a CRUD API (from the new interactive flow)
        if api_info.get("is_crud", False):
            resource_name = api_info.get("resource_name", "resources")
            resource_schema = api_info.get(
                "resource_schema", {}
            ).copy()  # Make a copy to avoid modifying original
            examples = api_info.get("examples", [])

            # Merge fields from examples into schema to ensure consistency
            if examples:
                # First pass: add missing fields from examples to schema
                for example in examples:
                    for field_name, field_value in example.items():
                        if field_name not in resource_schema:
                            # Infer type from the example value
                            if isinstance(field_value, int):
                                resource_schema[field_name] = "integer"
                            elif isinstance(field_value, bool):
                                resource_schema[field_name] = "boolean"
                            elif isinstance(field_value, float):
                                resource_schema[field_name] = "number"
                            else:
                                resource_schema[field_name] = "string"

                # Second pass: normalize examples to use 'id' instead of resource-specific id fields
                normalized_examples = []
                for example in examples:
                    normalized_example = {}
                    for field_name, field_value in example.items():
                        # Convert resource_id variations to 'id'
                        if (
                            field_name.endswith("_id")
                            and field_name == f"{resource_name[:-1]}_id"
                        ):
                            normalized_example["id"] = field_value
                        else:
                            normalized_example[field_name] = field_value
                    normalized_examples.append(normalized_example)
                examples = normalized_examples
            else:
                examples = api_info.get("examples", [])

            # Generate standard CRUD endpoints
            endpoints = self._generate_crud_endpoints(resource_name)

            # Create the object definition
            singular_name = (
                resource_name[:-1] if resource_name.endswith("s") else resource_name
            )
            resource_object = {
                "name": singular_name.capitalize(),
                "fields": resource_schema,
            }

            # Add standard fields if not present
            if "id" not in resource_object["fields"]:
                resource_object["fields"]["id"] = "string"
            if "created_at" not in resource_object["fields"]:
                resource_object["fields"]["created_at"] = "string"
            if "updated_at" not in resource_object["fields"]:
                resource_object["fields"]["updated_at"] = "string"

            # Build the structured data
            structured_data = {"endpoints": endpoints, "objects": [resource_object]}

            # Build the complete spec
            spec = self._build_spec_from_structured_data(
                structured_data,
                api_info.get("name"),
                api_info.get("description"),
                examples,
            )

            final_spec = self._add_server_environments(spec, api_info.get("base_url"))
            return final_spec, structured_data

        # Generate CRUD API from endpoint descriptions
        elif "endpoint_descriptions" in api_info:
            endpoint_descriptions = api_info.get("endpoint_descriptions", "")
            # Extract resource name from the description
            resource_name = self._extract_resource_name(endpoint_descriptions)

            # Generate standard CRUD endpoints
            endpoints = self._generate_crud_endpoints(resource_name)

            # Create a minimal object schema
            singular_name = (
                resource_name[:-1] if resource_name.endswith("s") else resource_name
            )
            structured_data = {
                "endpoints": endpoints,
                "objects": [
                    {
                        "name": singular_name.capitalize(),
                        "fields": {
                            "id": "string",
                            "name": "string",
                            "created_at": "string",
                            "updated_at": "string",
                        },
                    }
                ],
            }

            # Build the complete spec
            spec = self._build_spec_from_structured_data(
                structured_data,
                api_info.get("name"),
                api_info.get("description"),
                api_info.get("examples"),
            )

            final_spec = self._add_server_environments(spec, api_info.get("base_url"))
            return final_spec, structured_data

        # If we get here, the API info format is not supported
        raise ValueError("Invalid API info format - missing required fields")

    def generate_spec(self, api_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI specification from API information.

        Args:
            api_info: Dictionary containing API details

        Returns:
            Generated OpenAPI specification as dict
        """
        spec, _ = self.generate_spec_with_json(api_info)
        return spec

    def _extract_path_parameters(self, path: str) -> list:
        """Extract path parameters from a path string.

        Args:
            path: Path string (e.g., '/locations/{id}')

        Returns:
            List of parameter dictionaries
        """
        # Find all path parameters (e.g., {id})
        param_matches = re.findall(r"\{([^}]+)\}", path)

        # Create parameter definitions for each path parameter
        parameters = []
        for param_name in param_matches:
            # Use string type for all parameters (including id for UUID support)
            param_type = "string"

            parameters.append(
                {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": param_type},
                    "description": f"{param_name} parameter",
                }
            )

        return parameters

    def _build_spec_from_structured_data(
        self,
        llm_response: Dict[str, Any],
        name: str = None,
        description: str = None,
        examples: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build complete OpenAPI spec from structured endpoint/object data.

        Args:
            llm_response: Dictionary with endpoints and objects
            name: API name
            description: API description
            examples: List of example objects to include in schema

        Returns:
            OpenAPI specification as dict
        """
        # Build paths section from simple endpoint definitions
        paths = {}
        for endpoint in llm_response.get("endpoints", []):
            path = endpoint["path"]
            method = endpoint["method"].lower()

            if path not in paths:
                paths[path] = {}

            # Find the resource object for this endpoint
            resource_name = None
            for obj in llm_response.get("objects", []):
                resource_name = obj["name"]
                break  # Just use the first object for now

            # Build response schema based on returns description and resource name
            returns = endpoint.get("returns", "object")
            operation_id = endpoint.get("operationId", "")

            if "array" in returns.lower():
                # Simple array response for all array operations (no pagination)
                if resource_name:
                    response_schema = {
                        "type": "array",
                        "items": {"$ref": f"#/components/schemas/{resource_name}"},
                    }
                elif "object" in returns.lower():
                    response_schema = {"type": "array", "items": {"type": "object"}}
                else:
                    response_schema = {"type": "array", "items": {"type": "string"}}
            elif returns.lower() == "empty":
                response_schema = {"type": "object"}
            else:
                # Single object response
                if resource_name:
                    response_schema = {"$ref": f"#/components/schemas/{resource_name}"}
                else:
                    response_schema = {"type": "object"}

            responses = {
                "200": {
                    "description": "Success",
                    "content": {"application/json": {"schema": response_schema}},
                },
                "400": {
                    "description": "Bad Request",
                    "content": {
                        "application/problem+json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "title": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "detail": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "401": {
                    "description": "Unauthorized",
                    "content": {
                        "application/problem+json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "title": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "detail": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "500": {
                    "description": "Internal Server Error",
                    "content": {
                        "application/problem+json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "title": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "detail": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "503": {
                    "description": "Service Unavailable",
                    "content": {
                        "application/problem+json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "title": {"type": "string"},
                                    "status": {"type": "integer"},
                                    "detail": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            }

            # Extract path parameters and add them to the operation
            path_parameters = self._extract_path_parameters(path)

            operation = {
                "summary": endpoint.get("description", ""),
                "description": endpoint.get("description", ""),
                "operationId": endpoint.get("operationId", ""),
                "responses": responses,
            }

            # Add parameters section if there are path parameters
            if path_parameters:
                operation["parameters"] = path_parameters

            # Add request body for POST and PUT operations
            if method in ["post", "put"] and resource_name:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{resource_name}"}
                        }
                    },
                }

            paths[path][method] = operation

        # Build schemas section from simple object definitions
        schemas = {}
        for obj in llm_response.get("objects", []):
            properties = {}
            required = []

            # Convert simple field definitions to OpenAPI properties
            for field_name, field_type in obj.get("fields", {}).items():
                if field_type == "integer":
                    properties[field_name] = {"type": "integer"}
                elif field_type == "number":
                    properties[field_name] = {"type": "number"}
                elif field_type == "string":
                    properties[field_name] = {"type": "string"}
                elif field_type == "boolean":
                    properties[field_name] = {"type": "boolean"}
                else:
                    # Default to string for unknown types
                    properties[field_name] = {"type": "string"}

                # Make fields required except for system-generated ones
                if field_name not in ["id", "created_at", "updated_at"]:
                    required.append(field_name)

            schema_def = {
                "type": "object",
                "properties": properties,
                "required": required,
            }

            # Add examples if provided
            if examples and len(examples) > 0:
                # Use the first example as the main example
                schema_def["example"] = examples[0]

            schemas[obj["name"]] = schema_def

        # Add standard Error schema (RFC 7807)
        schemas["Error"] = {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "title": {"type": "string"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
            },
            "required": ["type", "title", "status", "detail"],
        }

        # Add RFC 7807 ValidationError schema
        schemas["ValidationError"] = {
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

        # Build the complete OpenAPI spec
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": name or "API",
                "description": description or "",
                "version": "1.0.0",
            },
            "servers": [
                {"url": "http://localhost:8000", "description": "Development server"},
                {"url": "https://test-api.example.com", "description": "Test server"},
                {
                    "url": "https://staging-api.example.com",
                    "description": "Staging server",
                },
                {"url": "https://api.example.com", "description": "Production server"},
            ],
            "paths": paths,
            "components": {"schemas": schemas},
        }

        return spec

    def _resolve_schema_refs(self, schema: Any, schemas_list: list) -> Any:
        """Resolve $ref references with inline schemas.

        Args:
            schema: Schema to resolve references in
            schemas_list: List of schemas to resolve references from

        Returns:
            Schema with resolved references
        """
        if isinstance(schema, dict):
            if "$ref" in schema:
                # Extract schema name from $ref
                ref = schema["$ref"]
                if ref.startswith("#/schemas/"):
                    schema_name = ref.replace("#/schemas/", "")
                    # Find the schema in our schemas list
                    for s in schemas_list:
                        if s.get("name") == schema_name:
                            return {
                                "type": s.get("type", "object"),
                                "properties": s.get("properties", {}),
                                "required": s.get("required", []),
                            }
                return schema  # If ref not found, return as-is
            else:
                # Recursively resolve refs in nested structures
                resolved = {}
                for key, value in schema.items():
                    resolved[key] = self._resolve_schema_refs(value, schemas_list)
                return resolved
        elif isinstance(schema, list):
            return [self._resolve_schema_refs(item, schemas_list) for item in schema]
        else:
            return schema

    def _add_server_environments(
        self, spec: Dict[str, Any], base_url: str = None
    ) -> Dict[str, Any]:
        """Add multiple server environments to the OpenAPI spec.

        Args:
            spec: OpenAPI specification dict
            base_url: Optional base URL from user input

        Returns:
            Updated OpenAPI specification with servers
        """
        if base_url:
            # Use user-provided base URL
            servers = [
                {"url": "http://localhost:8000", "description": "Development server"}
            ]

            # Clean base_url if it includes protocol
            clean_base_url = base_url.replace("https://", "").replace("http://", "")

            servers.extend(
                [
                    {
                        "url": f"https://test-{clean_base_url}",
                        "description": "Test server",
                    },
                    {
                        "url": f"https://staging-{clean_base_url}",
                        "description": "Staging server",
                    },
                    {
                        "url": f"https://{clean_base_url}",
                        "description": "Production server",
                    },
                ]
            )

            spec["servers"] = servers
            return spec
        else:
            # Fall back to default servers if already not set
            if "servers" not in spec:
                spec["servers"] = [
                    {
                        "url": "http://localhost:8000",
                        "description": "Development server",
                    },
                    {
                        "url": "https://test-api.example.com",
                        "description": "Test server",
                    },
                    {
                        "url": "https://staging-api.example.com",
                        "description": "Staging server",
                    },
                    {
                        "url": "https://api.example.com",
                        "description": "Production server",
                    },
                ]
            return spec

    def interactive_generate(self, prompt_file: Optional[str] = None) -> Dict[str, Any]:
        """Interactively prompt user for API details and generate spec.

        Args:
            prompt_file: Optional path to a saved prompt file

        Returns:
            Generated OpenAPI specification
        """
        return self.interactive.interactive_generate(prompt_file)

    def save_spec(
        self, spec: Dict[str, Any], output_path: str, format: str = "yaml"
    ) -> str:
        """Save generated spec to file.

        Args:
            spec: OpenAPI specification dict
            output_path: Path to save the spec
            format: Output format ("yaml" or "json")

        Returns:
            Path to saved file
        """
        path = Path(output_path)

        if format == "yaml":
            if not path.suffix:
                path = path.with_suffix(".yaml")
            with open(path, "w") as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
        else:
            if not path.suffix:
                path = path.with_suffix(".json")
            with open(path, "w") as f:
                json.dump(spec, f, indent=2)

        return str(path)

    def _save_prompt(self, api_info: Dict[str, Any], spec: Dict[str, Any]) -> None:
        """Save prompt data for future regeneration (compatibility method).

        This is a compatibility method that delegates to the interactive generator.

        Args:
            api_info: API information dictionary
            spec: Generated OpenAPI spec
        """
        # Create a minimal LLM JSON response for compatibility
        llm_json = {"endpoints": [], "objects": []}
        self.interactive.save_prompt_and_json(api_info, spec, llm_json)

    def load_prompt(self, prompt_file: str) -> Dict[str, Any]:
        """Load saved prompt data (compatibility method).

        Args:
            prompt_file: Path to the prompt file

        Returns:
            API information dictionary
        """
        return self.interactive.load_prompt(prompt_file)

    def _schema_modified_since_prompt(
        self, prompt_file: str, schema_file: Path
    ) -> bool:
        """Check if schema file has been modified since prompt was created (compatibility method).

        Args:
            prompt_file: Path to the prompt file
            schema_file: Path to the schema file

        Returns:
            True if schema file is newer than prompt file
        """
        return self.interactive.schema_modified_since_prompt(prompt_file, schema_file)

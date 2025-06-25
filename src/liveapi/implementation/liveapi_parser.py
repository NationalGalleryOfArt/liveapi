"""LiveAPI-specific OpenAPI parser that identifies CRUD+ patterns."""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import prance
from .pydantic_generator import PydanticGenerator


class LiveAPIParser:
    """Parser that identifies and maps CRUD+ resources in OpenAPI specs.

    This parser identifies resources that follow the CRUD+ pattern and
    automatically maps them to standard handlers.
    """

    def __init__(self, spec_path: str, backend_type: str = "sqlmodel"):
        self.spec_path = Path(spec_path)
        self.spec = None
        self.pydantic_generator = PydanticGenerator(backend_type=backend_type)

    def load_spec(self):
        """Load OpenAPI specification from file."""
        if not self.spec_path.exists():
            raise FileNotFoundError(f"OpenAPI spec not found: {self.spec_path}")

        # Use prance to parse the OpenAPI spec
        self.spec = prance.BaseParser(str(self.spec_path), strict=False).specification
        return self.spec

    def identify_crud_resources(self) -> Dict[str, Dict[str, Any]]:
        """Identify resources that follow the CRUD+ pattern.

        Returns:
            Dict mapping resource names to their CRUD operations
        """
        if not self.spec:
            self.load_spec()

        # Pass schema definitions to Pydantic generator
        if "components" in self.spec:
            self.pydantic_generator.set_schema_definitions(self.spec["components"])

        paths = self.spec.get("paths", {})
        resources = {}

        for path, path_item in paths.items():
            resource_info = self._extract_resource_from_path(path)
            if not resource_info:
                continue

            resource_name, is_item_path = resource_info

            if resource_name not in resources:
                resources[resource_name] = {
                    "name": resource_name,
                    "operations": {},
                    "model": None,
                    "paths": {"collection": None, "item": None},
                }

            if is_item_path:
                resources[resource_name]["paths"]["item"] = path
            else:
                resources[resource_name]["paths"]["collection"] = path

            for method in ["get", "post", "put", "patch", "delete"]:
                operation = path_item.get(method)
                if not operation:
                    continue

                operation_type = self._categorize_operation(
                    method, is_item_path, operation
                )

                if operation_type:
                    resources[resource_name]["operations"][operation_type] = {
                        "method": method,
                        "path": path,
                        "operation": operation,
                    }

                # Since all resources are CRUD, we just need to find the model
                if not resources[resource_name]["model"]:
                    model = self._extract_model_from_operation(operation, method)
                    if model:
                        resources[resource_name]["model"] = model

        return resources

    def _extract_resource_from_path(self, path: str) -> Optional[Tuple[str, bool]]:
        """Extract resource name from an API path.

        Args:
            path: API path like /users or /users/{id}

        Returns:
            Tuple of (resource_name, is_item_path) or None
        """
        parts = path.strip("/").split("/")
        if not parts:
            return None

        # Simple heuristic: first part is usually the resource
        resource_name = parts[0]

        # Check if this is an item path (has ID parameter)
        is_item_path = any(
            part.startswith("{") and part.endswith("}") for part in parts
        )

        return resource_name, is_item_path

    def _categorize_operation(
        self, method: str, is_item_path: bool, operation: Dict[str, Any]
    ) -> Optional[str]:
        """Categorize an operation as a CRUD+ operation type.

        Returns operation type: create, read, update, delete, list, or None
        """
        method = method.lower()

        if method == "post" and not is_item_path:
            return "create"
        elif method == "get" and is_item_path:
            return "read"
        elif method == "get" and not is_item_path:
            return "list"
        elif method == "put" and is_item_path:
            return "update"
        elif method == "patch" and is_item_path:
            return "update_partial"
        elif method == "delete" and is_item_path:
            return "delete"

        return None

    def _extract_model_from_operation(
        self, operation: Dict[str, Any], method: str
    ) -> Optional[Any]:
        """Extract Pydantic model from operation definition."""
        # Try request body first (for POST/PUT/PATCH)
        if method in ["post", "put", "patch"]:
            request_body = operation.get("requestBody")
            if request_body and "content" in request_body:
                content = request_body["content"]
                if "application/json" in content:
                    schema = content["application/json"].get("schema")
                    if schema:
                        model_name = operation.get("operationId", "Resource") + "Model"
                        return self.pydantic_generator.generate_model_from_schema(
                            schema, model_name
                        )

        # Try response schema (for GET)
        responses = operation.get("responses", {})
        for status_code, response in responses.items():
            if status_code.startswith("2") and "content" in response:
                content = response["content"]
                if "application/json" in content:
                    schema = content["application/json"].get("schema")
                    if schema:
                        # Handle array responses for list operations
                        if schema.get("type") == "array" and "items" in schema:
                            item_schema = schema["items"]
                            model_name = (
                                operation.get("operationId", "Resource") + "Model"
                            )
                            return self.pydantic_generator.generate_model_from_schema(
                                item_schema, model_name
                            )
                        elif schema.get("type") == "object":
                            model_name = (
                                operation.get("operationId", "Resource") + "Model"
                            )
                            return self.pydantic_generator.generate_model_from_schema(
                                schema, model_name
                            )

        return None

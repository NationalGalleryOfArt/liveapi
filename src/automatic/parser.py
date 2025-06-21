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

        # Look for JSON content first
        if "application/json" in content:
            return content["application/json"].get("schema")

        # Fallback to first available content type
        if content:
            first_content = next(iter(content.values()))
            return first_content.get("schema")

        return None

    def _extract_responses(self, operation) -> Dict[str, Any]:
        """Extract response schemas from operation."""
        return operation.get("responses", {})

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

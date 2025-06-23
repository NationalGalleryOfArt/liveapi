"""TypedDict generation from OpenAPI schemas."""

from typing import Dict, List, Any, Set, Optional, Tuple


class TypedDictGenerator:
    """Generates TypedDict classes from OpenAPI schemas."""

    def __init__(self):
        self.generated_types: Set[str] = set()

    def generate_types_for_routes(self, routes: List[Dict[str, Any]]) -> str:
        """Generate all TypedDict classes for request/response schemas."""
        imports = [
            "from typing import Dict, List, Any, Optional, Union",
            "from typing_extensions import TypedDict, NotRequired",
            "",
        ]

        type_definitions = []
        self.generated_types.clear()

        # Track schema references and their resolved schemas
        schema_refs = {}

        # First pass: collect all schema references from routes
        for route in routes:
            # Check request body for schema references
            request_body = route.get("request_body", {})
            if request_body:
                # Check for x-schema-name which indicates a resolved reference
                if "x-schema-name" in request_body:
                    schema_name = request_body["x-schema-name"]
                    schema_refs[schema_name] = request_body
                # Check for original_ref which indicates a resolved reference
                elif "original_ref" in request_body:
                    ref_name = self._extract_schema_name_from_ref(
                        request_body["original_ref"]
                    )
                    schema_refs[ref_name] = request_body

            # Check response schemas for references
            for response in route.get("responses", {}).values():
                if isinstance(response, dict) and "content" in response:
                    for content_type, content in response["content"].items():
                        if "schema" in content:
                            schema = content["schema"]
                            # Check for x-schema-name which indicates a resolved reference
                            if "x-schema-name" in schema:
                                schema_name = schema["x-schema-name"]
                                schema_refs[schema_name] = schema
                            # Check for original_ref which indicates a resolved reference
                            elif "original_ref" in schema:
                                ref_name = self._extract_schema_name_from_ref(
                                    schema["original_ref"]
                                )
                                schema_refs[ref_name] = schema
                            # Check for array items with references
                            elif schema.get("type") == "array" and "items" in schema:
                                items = schema["items"]
                                if "x-schema-name" in items:
                                    schema_name = items["x-schema-name"]
                                    schema_refs[schema_name] = items
                                elif "original_ref" in items:
                                    ref_name = self._extract_schema_name_from_ref(
                                        items["original_ref"]
                                    )
                                    schema_refs[ref_name] = items

        # Generate types for schema references first
        for schema_name, schema in schema_refs.items():
            if schema_name not in self.generated_types:
                type_def = self._schema_to_typeddict(schema, schema_name)
                if type_def:
                    type_definitions.append(type_def)

        # Generate types for routes
        for route in routes:
            # Generate request types
            if route.get("request_body"):
                request_type = self._generate_request_type(route)
                if request_type:
                    type_definitions.append(request_type)

            # Generate response types
            response_types = self._generate_response_types(route)
            type_definitions.extend(response_types)

        if not type_definitions:
            return ""

        return "\n".join(imports + type_definitions)

    def _extract_schema_name_from_ref(self, ref: str) -> str:
        """Extract schema name from a reference string."""
        if not ref or not isinstance(ref, str):
            return "Unknown"

        if not ref.startswith("#/"):
            return "Unknown"

        # Parse the reference path and get the last part
        parts = ref.lstrip("#/").split("/")
        if parts:
            return parts[-1]

        return "Unknown"

    def _generate_request_type(self, route: Dict[str, Any]) -> str:
        """Generate TypedDict for request body schema."""
        operation_id = route["operation_id"]
        schema = route["request_body"]

        if not schema:
            return ""

        # Check if this is a reference to an existing schema
        if "x-schema-name" in schema:
            schema_name = schema["x-schema-name"]
            if schema_name in self.generated_types:
                # We've already generated this type, so just create an alias
                class_name = self._operation_to_request_class_name(operation_id)
                if class_name != schema_name and class_name not in self.generated_types:
                    self.generated_types.add(class_name)
                    return f"{class_name} = {schema_name}"
                return ""

        # Generate a new type
        class_name = self._operation_to_request_class_name(operation_id)
        return self._schema_to_typeddict(schema, class_name)

    def _generate_response_types(self, route: Dict[str, Any]) -> List[str]:
        """Generate TypedDict classes for response schemas."""
        operation_id = route["operation_id"]
        responses = route.get("responses", {})

        type_definitions = []

        for status_code, response_info in responses.items():
            if not isinstance(response_info, dict):
                continue

            content = response_info.get("content", {})

            # Try application/json first
            if "application/json" in content:
                schema = content["application/json"].get("schema")
                if schema:
                    # Check if this is a reference to an existing schema
                    if "x-schema-name" in schema or "ref_name" in schema:
                        schema_name = schema.get("x-schema-name") or schema.get(
                            "ref_name"
                        )
                        if schema_name in self.generated_types:
                            # We've already generated this type, so just create an alias
                            class_name = self._operation_to_response_class_name(
                                operation_id, status_code
                            )
                            if (
                                class_name != schema_name
                                and class_name not in self.generated_types
                            ):
                                self.generated_types.add(class_name)
                                type_definitions.append(f"{class_name} = {schema_name}")
                            continue

                    # Handle array responses
                    if schema.get("type") == "array" and "items" in schema:
                        items = schema["items"]
                        if "x-schema-name" in items or "ref_name" in items:
                            item_schema_name = items.get("x-schema-name") or items.get(
                                "ref_name"
                            )
                            if item_schema_name in self.generated_types:
                                # We've already generated the item type, so create an array alias
                                class_name = self._operation_to_response_class_name(
                                    operation_id, status_code
                                )
                                if class_name not in self.generated_types:
                                    self.generated_types.add(class_name)
                                    type_definitions.append(
                                        f"{class_name} = List[{item_schema_name}]"
                                    )
                                continue

                    # Generate a new type
                    class_name = self._operation_to_response_class_name(
                        operation_id, status_code
                    )
                    type_def = self._schema_to_typeddict(schema, class_name)
                    if type_def:
                        type_definitions.append(type_def)

            # If no application/json, try the first available content type
            elif content:
                first_content_type = next(iter(content.keys()))
                schema = content[first_content_type].get("schema")
                if schema:
                    class_name = self._operation_to_response_class_name(
                        operation_id, status_code
                    )
                    type_def = self._schema_to_typeddict(schema, class_name)
                    if type_def:
                        type_definitions.append(type_def)

        return type_definitions

    def _schema_to_typeddict(self, schema: Dict[str, Any], class_name: str) -> str:
        """Convert OpenAPI schema to TypedDict class definition."""
        if class_name in self.generated_types:
            return ""

        self.generated_types.add(class_name)

        # Handle array schemas
        if schema.get("type") == "array" and "items" in schema:
            items_schema = schema["items"]
            # Use a simpler name for the item type
            item_class_name = self._simplify_class_name(f"{class_name}Item")
            item_type, nested_types = self._get_field_type_and_nested(
                items_schema, item_class_name
            )

            # If we have nested types, add them first
            if nested_types:
                return f"{nested_types}\n\n{class_name} = List[{item_type}]"
            else:
                return f"{class_name} = List[{item_type}]"

        # Handle non-object schemas
        if schema.get("type") and schema.get("type") != "object":
            python_type = self._schema_to_python_type(schema)
            return f"{class_name} = {python_type}"

        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        if not properties:
            return f"class {class_name}(TypedDict):\n    pass\n"

        fields = []
        nested_types = []

        for field_name, field_schema in properties.items():
            # Use a simpler name for nested types
            nested_class_name = self._simplify_class_name(field_name.capitalize())
            field_type, nested_type = self._get_field_type_and_nested(
                field_schema, nested_class_name, field_name
            )

            if nested_type:
                nested_types.append(nested_type)

            # Add field with appropriate required/optional annotation
            if field_name in required_fields:
                fields.append(f"    {field_name}: {field_type}")
            else:
                fields.append(f"    {field_name}: NotRequired[{field_type}]")

        class_def = f"class {class_name}(TypedDict):\n" + "\n".join(fields) + "\n"

        # Return nested types first, then main class
        if nested_types:
            return "\n".join(nested_types) + "\n\n" + class_def
        return class_def

    def _simplify_class_name(self, field_name: str) -> str:
        """Simplify class names for nested types."""
        # For common field names, use standard type names
        common_fields = {
            "User": "User",
            "Profile": "Profile",
            "Settings": "Settings",
            "Config": "Config",
            "Options": "Options",
            "Metadata": "Metadata",
            "Data": "Data",
            "Item": "Item",
            "Items": "Item",  # Singular for array items
            "NestedObject": "NestedObject",
        }

        # Check if the field name is in our common fields dictionary
        if field_name in common_fields:
            return common_fields[field_name]

        # Otherwise, return the field name as is
        return field_name

    def _get_field_type_and_nested(
        self, field_schema: Dict[str, Any], nested_name: str, field_name: str = ""
    ) -> Tuple[str, Optional[str]]:
        """Get the field type and any nested type definitions."""
        # Check for schema reference
        if "x-schema-name" in field_schema:
            schema_name = field_schema["x-schema-name"]
            return schema_name, None

        if "ref_name" in field_schema:
            schema_name = field_schema["ref_name"]
            return schema_name, None

        # Handle array type
        if field_schema.get("type") == "array" and "items" in field_schema:
            items = field_schema["items"]

            # Check for reference in items
            if "x-schema-name" in items:
                item_type = items["x-schema-name"]
                return f"List[{item_type}]", None

            if "ref_name" in items:
                item_type = items["ref_name"]
                return f"List[{item_type}]", None

            # Handle nested object in array items
            if items.get("type") == "object" and "properties" in items:
                # Use a simpler name for the nested object
                item_class_name = self._simplify_class_name("NestedObject")
                nested_def = self._schema_to_typeddict(items, item_class_name)
                return f"List[{item_class_name}]", nested_def

            # Handle other array items
            item_type = self._schema_to_python_type(items)
            if isinstance(item_type, tuple):
                actual_type, nested_def = item_type
                return f"List[{actual_type}]", nested_def

            return f"List[{item_type}]", None

        # Handle object type (nested object)
        if field_schema.get("type") == "object" and "properties" in field_schema:
            # Generate a nested TypedDict for this object
            nested_def = self._schema_to_typeddict(field_schema, nested_name)
            return nested_name, nested_def

        # Handle primitive types
        return self._schema_to_python_type(field_schema, field_name), None

    def _schema_to_python_type(
        self, schema: Dict[str, Any], field_name: str = ""
    ) -> str:
        """Convert OpenAPI schema type to Python type annotation."""
        # Handle schema references
        if "$ref" in schema:
            # For references, use the last part of the reference as the type name
            ref_parts = schema["$ref"].split("/")
            ref_name = ref_parts[-1]
            return ref_name

        # Handle x-schema-name which indicates a resolved reference
        if "x-schema-name" in schema:
            return schema["x-schema-name"]

        # Handle ref_name which indicates a resolved reference
        if "ref_name" in schema:
            return schema["ref_name"]

        schema_type = schema.get("type", "string")

        if schema_type == "string":
            format_type = schema.get("format")
            if format_type == "date-time":
                return "str  # date-time"
            elif format_type == "date":
                return "str  # date"
            elif format_type == "email":
                return "str  # email"
            elif format_type == "uuid":
                return "str  # uuid"
            return "str"
        elif schema_type == "integer":
            return "int"
        elif schema_type == "number":
            return "float"
        elif schema_type == "boolean":
            return "bool"
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            if items_schema:
                # Handle reference in items
                if "$ref" in items_schema:
                    ref_parts = items_schema["$ref"].split("/")
                    ref_name = ref_parts[-1]
                    return f"List[{ref_name}]"

                # Handle x-schema-name in items
                if "x-schema-name" in items_schema:
                    return f"List[{items_schema['x-schema-name']}]"

                # Handle ref_name in items
                if "ref_name" in items_schema:
                    return f"List[{items_schema['ref_name']}]"

                # Handle nested object in array items
                if (
                    items_schema.get("type") == "object"
                    and "properties" in items_schema
                ):
                    return f"List[{self._simplify_class_name('NestedObject')}]"

                # Handle regular items
                item_type = self._schema_to_python_type(items_schema)
                return f"List[{item_type}]"
            return "List[Any]"
        elif schema_type == "object":
            # For generic objects without properties
            if "properties" not in schema:
                return "Dict[str, Any]"
            # For objects with properties, use a proper type name based on field name or context
            if field_name.lower() == "metadata":
                return "Metadata"
            return "Dict[str, Any]"
        else:
            return "Any"

    def _operation_to_request_class_name(self, operation_id: str) -> str:
        """Convert operation ID to request class name."""
        # create_user -> CreateUserRequest
        name = self._snake_to_pascal(operation_id)
        return f"{name}Request"

    def _operation_to_response_class_name(
        self, operation_id: str, status_code: str
    ) -> str:
        """Convert operation ID and status to response class name."""
        # create_user, 201 -> CreateUserResponse
        name = self._snake_to_pascal(operation_id)
        if status_code.startswith("2"):  # Success responses
            return f"{name}Response"
        else:  # Error responses
            return f"{name}ErrorResponse"

    def _field_to_class_name(self, field_name: str) -> str:
        """Convert field name to nested class name."""
        # user_profile -> UserProfile
        return self._snake_to_pascal(field_name) or "NestedObject"

    def _snake_to_pascal(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        if not snake_str:
            return ""
        components = snake_str.split("_")
        return "".join(word.capitalize() for word in components if word)

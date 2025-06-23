"""Dynamic Pydantic model generation from OpenAPI schemas."""

from typing import Dict, List, Any, Optional, Type, Union, get_args
from pydantic import BaseModel, create_model, Field
from pydantic.fields import FieldInfo


class PydanticGenerator:
    """Generates Pydantic models dynamically from OpenAPI schemas."""

    def __init__(self):
        self.generated_models: Dict[str, Type[BaseModel]] = {}
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    def set_schema_definitions(self, components: Dict[str, Any]) -> None:
        """Store schema definitions from OpenAPI components."""
        if components and "schemas" in components:
            self._schema_cache = components["schemas"]

    def generate_model_from_schema(
        self,
        schema: Dict[str, Any],
        model_name: str,
        required_fields: Optional[List[str]] = None,
    ) -> Type[BaseModel]:
        """Generate a Pydantic model from an OpenAPI schema."""
        # Check if already generated
        if model_name in self.generated_models:
            return self.generated_models[model_name]

        # Handle schema references
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            if ref_name in self._schema_cache:
                schema = self._schema_cache[ref_name]
                model_name = ref_name
            else:
                # Return a simple dict model if reference not found
                return self._create_dict_model(model_name)

        # Handle non-object schemas
        if schema.get("type") != "object":
            return self._create_simple_model(schema, model_name)

        # Build field definitions
        field_definitions = {}
        properties = schema.get("properties", {})
        required = set(required_fields or schema.get("required", []))

        for field_name, field_schema in properties.items():
            field_type = self._schema_to_python_type(field_schema, field_name)

            # Determine if field is required
            if field_name in required:
                default = ...  # Required field
            else:
                default = None  # Optional field
                field_type = Optional[field_type]

            # Add field description if available
            description = field_schema.get("description", None)
            field_info = Field(default=default, description=description)

            field_definitions[field_name] = (field_type, field_info)

        # Create the model
        model = create_model(model_name, __base__=BaseModel, **field_definitions)
        
        # Add example to the model if it exists in the schema
        if "example" in schema:
            # Create a Config class with the example (Pydantic v2 syntax)
            config_attrs = {
                "json_schema_extra": {
                    "example": schema["example"]
                }
            }
            # Add Config to model
            model.model_config = config_attrs

        # Cache the model
        self.generated_models[model_name] = model
        return model

    def _schema_to_python_type(
        self, schema: Dict[str, Any], field_name: str = ""
    ) -> Any:
        """Convert OpenAPI schema to Python type annotation."""
        # Handle references
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            # Generate the referenced model if needed
            if ref_name in self._schema_cache:
                return self.generate_model_from_schema(
                    self._schema_cache[ref_name], ref_name
                )
            return Dict[str, Any]

        schema_type = schema.get("type", "string")

        if schema_type == "string":
            return str
        elif schema_type == "integer":
            return int
        elif schema_type == "number":
            return float
        elif schema_type == "boolean":
            return bool
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            if items_schema:
                item_type = self._schema_to_python_type(items_schema)
                return List[item_type]
            return List[Any]
        elif schema_type == "object":
            # Generate nested model
            nested_model_name = self._field_to_model_name(field_name)
            return self.generate_model_from_schema(schema, nested_model_name)
        else:
            return Any

    def _create_dict_model(self, model_name: str) -> Type[BaseModel]:
        """Create a simple dict-based model."""
        return create_model(
            model_name, __base__=BaseModel, __root__=(Dict[str, Any], ...)
        )

    def _create_simple_model(
        self, schema: Dict[str, Any], model_name: str
    ) -> Type[BaseModel]:
        """Create a model for non-object schemas."""
        schema_type = schema.get("type", "string")

        if schema_type == "array":
            item_type = self._schema_to_python_type(schema.get("items", {}))
            root_type = List[item_type]
        else:
            root_type = self._schema_to_python_type(schema)

        return create_model(model_name, __base__=BaseModel, __root__=(root_type, ...))

    def _field_to_model_name(self, field_name: str) -> str:
        """Convert field name to model name."""
        if not field_name:
            return "NestedModel"
        # Convert snake_case to PascalCase
        components = field_name.split("_")
        return "".join(word.capitalize() for word in components if word)

    def generate_request_model(
        self, route: Dict[str, Any]
    ) -> Optional[Type[BaseModel]]:
        """Generate a Pydantic model for request body."""
        request_body = route.get("request_body")
        if not request_body:
            return None

        operation_id = route.get("operation_id", "Unknown")
        model_name = f"{self._snake_to_pascal(operation_id)}Request"

        return self.generate_model_from_schema(request_body, model_name)

    def generate_response_model(
        self, route: Dict[str, Any], status_code: str = "200"
    ) -> Optional[Type[BaseModel]]:
        """Generate a Pydantic model for response."""
        responses = route.get("responses", {})
        response_schema = responses.get(status_code, {})

        if not response_schema:
            return None

        content = response_schema.get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema")
            if schema:
                operation_id = route.get("operation_id", "Unknown")
                model_name = f"{self._snake_to_pascal(operation_id)}Response"
                return self.generate_model_from_schema(schema, model_name)

        return None

    def _snake_to_pascal(self, snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        if not snake_str:
            return ""
        components = snake_str.split("_")
        return "".join(word.capitalize() for word in components if word)

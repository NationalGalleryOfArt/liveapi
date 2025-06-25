"""Dynamic Pydantic model generation from OpenAPI schemas."""

from typing import Dict, List, Any, Optional, Type, Union
from pydantic import BaseModel, create_model, Field
from datetime import datetime


class PydanticGenerator:
    """Generates Pydantic models dynamically from OpenAPI schemas."""

    def __init__(self, backend_type: str = "sqlmodel"):
        """Initialize the generator.

        Args:
            backend_type: Backend type - "default" for in-memory, "sqlmodel" for SQL (default)
        """
        self.backend_type = backend_type
        self.generated_models: Dict[str, Type[Union[BaseModel, Any]]] = {}
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

        # Import SQLModel only when needed
        self._sqlmodel_base = None
        if backend_type == "sqlmodel":
            try:
                from sqlmodel import SQLModel

                self._sqlmodel_base = SQLModel
            except ImportError:
                raise ImportError(
                    "SQLModel is required for SQL backend. Install with: pip install sqlmodel"
                )

    def set_schema_definitions(self, components: Dict[str, Any]) -> None:
        """Store schema definitions from OpenAPI components."""
        if components and "schemas" in components:
            self._schema_cache = components["schemas"]

    def generate_model_from_schema(
        self,
        schema: Dict[str, Any],
        model_name: str,
        required_fields: Optional[List[str]] = None,
        table_name: Optional[str] = None,
    ) -> Type[Union[BaseModel, Any]]:
        """Generate a Pydantic or SQLModel from an OpenAPI schema."""
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

            # Handle SQLModel Field vs Pydantic Field
            if self.backend_type == "sqlmodel":
                from sqlmodel import Field as SQLField

                # Determine if field is required and configure for SQLModel
                if field_name == "id":  # Special handling for ID field
                    field_info = SQLField(default=None, primary_key=True)
                    field_type = Optional[field_type]
                elif field_name in required:
                    field_info = SQLField()
                else:
                    field_info = SQLField(default=None)
                    field_type = Optional[field_type]

                # Add description if available
                description = field_schema.get("description", None)
                if description:
                    field_info.description = description
            else:
                # Standard Pydantic Field
                if field_name in required:
                    default = ...  # Required field
                else:
                    default = None  # Optional field
                    field_type = Optional[field_type]

                # Add field description if available
                description = field_schema.get("description", None)
                field_info = Field(default=default, description=description)

            field_definitions[field_name] = (field_type, field_info)

        # Choose base class and create model
        if self.backend_type == "sqlmodel":
            # Create SQLModel table
            if not table_name:
                table_name = model_name.lower() + "s"  # pluralize for table name

            # For SQLModel, use create_model approach with proper SQLModel base
            from sqlmodel import SQLModel

            # Use create_model for SQLModel - this avoids the type resolution issues
            # First, prepare field definitions for create_model format
            create_model_fields = {}
            for field_name, (field_type, field_info) in field_definitions.items():
                create_model_fields[field_name] = (field_type, field_info)

            # Create the model with table=True configuration
            model = create_model(
                model_name,
                __base__=SQLModel,
                __config__={"table": True},
                __tablename__=table_name,
                **create_model_fields,
            )

            # Add example to the model if it exists in the schema
            if "example" in schema:
                model.model_config = {
                    "json_schema_extra": {"example": schema["example"]}
                }
        else:
            base_class = BaseModel
            # Create the model
            model = create_model(model_name, __base__=base_class, **field_definitions)

            # Add example to the model if it exists in the schema
            if "example" in schema:
                # Create a Config class with the example (Pydantic v2 syntax)
                config_attrs = {"json_schema_extra": {"example": schema["example"]}}
                # Add Config to model
                model.model_config = config_attrs

        # Manually construct the model source
        model_source = f"class {model_name}(SQLModel, table=True):\n"
        for field_name, (field_type, field_info) in field_definitions.items():
            type_str = self._type_to_string(field_type)
            field_args = []
            if field_info.default is not None:
                field_args.append(f"default={field_info.default!r}")
            if getattr(field_info, "primary_key", False):
                field_args.append("primary_key=True")
            if field_info.description:
                field_args.append(f"description={field_info.description!r}")

            field_str = f" = Field({', '.join(field_args)})" if field_args else ""
            model_source += f"    {field_name}: {type_str}{field_str}\n"

        model.model_source = model_source

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
            if "format" in schema and schema["format"] == "date-time":
                return datetime
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

    def _create_dict_model(self, model_name: str) -> Type[Union[BaseModel, Any]]:
        """Create a simple dict-based model."""
        if self.backend_type == "sqlmodel":
            from sqlmodel import SQLModel

            # Create a SQLModel table class
            class_attrs = {
                "__annotations__": {"__root__": Dict[str, Any]},
                "__root__": (...,),
                "__tablename__": model_name.lower() + "s",
            }
            model = type(model_name, (SQLModel,), class_attrs)
            model.model_config = {"table": True}
            return model
        else:
            return create_model(
                model_name, __base__=BaseModel, __root__=(Dict[str, Any], ...)
            )

    def _create_simple_model(
        self, schema: Dict[str, Any], model_name: str
    ) -> Type[Union[BaseModel, Any]]:
        """Create a model for non-object schemas."""
        schema_type = schema.get("type", "string")

        if schema_type == "array":
            item_type = self._schema_to_python_type(schema.get("items", {}))
            root_type = List[item_type]
        else:
            root_type = self._schema_to_python_type(schema)

        if self.backend_type == "sqlmodel":
            from sqlmodel import SQLModel

            # Create a SQLModel table class
            class_attrs = {
                "__annotations__": {"__root__": root_type},
                "__root__": (...,),
                "__tablename__": model_name.lower() + "s",
            }
            model = type(model_name, (SQLModel,), class_attrs)
            model.model_config = {"table": True}
            return model
        else:
            return create_model(
                model_name, __base__=BaseModel, __root__=(root_type, ...)
            )

    def _field_to_model_name(self, field_name: str) -> str:
        """Convert field name to model name."""
        if not field_name:
            return "NestedModel"
        # Convert snake_case to PascalCase
        components = field_name.split("_")
        return "".join(word.capitalize() for word in components if word)

    def generate_request_model(
        self, route: Dict[str, Any]
    ) -> Optional[Type[Union[BaseModel, Any]]]:
        """Generate a Pydantic or SQLModel for request body."""
        request_body = route.get("request_body")
        if not request_body:
            return None

        operation_id = route.get("operation_id", "Unknown")
        model_name = f"{self._snake_to_pascal(operation_id)}Request"

        return self.generate_model_from_schema(request_body, model_name)

    def generate_response_model(
        self, route: Dict[str, Any], status_code: str = "200"
    ) -> Optional[Type[Union[BaseModel, Any]]]:
        """Generate a Pydantic or SQLModel for response."""
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

    def _type_to_string(self, type_annotation) -> str:
        """Convert a type annotation to its string representation."""
        # Handle basic types
        if type_annotation == str:
            return "str"
        elif type_annotation == int:
            return "int"
        elif type_annotation == float:
            return "float"
        elif type_annotation == bool:
            return "bool"
        elif hasattr(type_annotation, "__name__"):
            return type_annotation.__name__
        elif hasattr(type_annotation, "__origin__"):
            # Handle generic types like Optional[str], List[int], etc.
            origin = type_annotation.__origin__
            args = getattr(type_annotation, "__args__", ())

            # Check if it's a Union type (which Optional uses)
            if origin is Union:
                if len(args) == 2 and type(None) in args:
                    # This is Optional[T]
                    non_none_type = args[0] if args[1] is type(None) else args[1]
                    return f"Optional[{self._type_to_string(non_none_type)}]"
            elif origin is list:
                if args:
                    return f"List[{self._type_to_string(args[0])}]"
                return "List[Any]"
            elif origin is dict:
                if len(args) >= 2:
                    return f"Dict[{self._type_to_string(args[0])}, {self._type_to_string(args[1])}]"
                return "Dict[str, Any]"

        # Fallback to string representation
        return str(type_annotation).replace("<class '", "").replace("'>", "")

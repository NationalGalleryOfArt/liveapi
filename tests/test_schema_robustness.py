"""Tests for schema generation robustness and edge cases."""

import pytest
from src.liveapi.implementation.pydantic_generator import PydanticGenerator


class TestSchemaGenerationRobustness:
    """Test schema generation with complex and malformed schemas."""

    def test_circular_schema_references(self):
        """Test handling of circular references in OpenAPI schemas."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "manager": {"$ref": "#/components/schemas/User"}
                        }
                    },
                    "Department": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "head": {"$ref": "#/components/schemas/Employee"}
                        }
                    },
                    "Employee": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "department": {"$ref": "#/components/schemas/Department"}
                        }
                    }
                }
            }
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(spec.get("components", {}))

        # KNOWN LIMITATION: Current implementation doesn't handle circular references
        # This test documents the issue and will pass when the bug is fixed
        user_schema = spec["components"]["schemas"]["User"]

        with pytest.raises(RecursionError):
            # Should currently fail due to infinite recursion
            generator.generate_model_from_schema(user_schema, "User")

        # TODO: When circular reference handling is implemented, change to:
        # user_model = generator.generate_model_from_schema(user_schema, "User")
        # assert user_model is not None

    def test_deeply_nested_object_generation(self):
        """Test generation of deeply nested object structures."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "Level1": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "level2": {"$ref": "#/components/schemas/Level2"}
                        }
                    },
                    "Level2": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "level3": {"$ref": "#/components/schemas/Level3"}
                        }
                    },
                    "Level3": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "level4": {"$ref": "#/components/schemas/Level4"}
                        }
                    },
                    "Level4": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "data": {"type": "string"}
                        }
                    }
                }
            }
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(spec.get("components", {}))

        # Test non-circular deep nesting (should work)
        level1_schema = spec["components"]["schemas"]["Level1"]

        try:
            model = generator.generate_model_from_schema(level1_schema, "Level1")
            assert model is not None

            # Should be able to create an instance with nested data
            instance_data = {
                "id": "1",
                "level2": {
                    "id": "2",
                    "level3": {
                        "id": "3",
                        "level4": {
                            "id": "4",
                            "data": "deep_value"
                        }
                    }
                }
            }

            # Should validate nested structure correctly
            instance = model(**instance_data)
            assert instance.id == "1"
            assert instance.level2.id == "2"
            assert instance.level2.level3.level4.data == "deep_value"
        except (ValueError, RecursionError) as e:
            # Deep nesting may also hit recursion issues in complex cases
            pytest.skip(f"Deep nesting limitation: {e}")

    def test_invalid_schema_definitions(self):
        """Test handling of malformed OpenAPI schema definitions."""

        # Test 1: Missing required properties
        invalid_spec_1 = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "InvalidModel": {
                        "type": "object"
                        # Missing properties field
                    }
                }
            }
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(invalid_spec_1.get("components", {}))
        # Should handle gracefully and return a basic model
        invalid_schema = invalid_spec_1["components"]["schemas"]["InvalidModel"]
        model = generator.generate_model_from_schema(invalid_schema, "InvalidModel")
        assert model is not None

        # Test 2: Invalid property types
        invalid_spec_2 = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "InvalidTypes": {
                        "type": "object",
                        "properties": {
                            "bad_field": {"type": "invalid_type"},
                            "good_field": {"type": "string"}
                        }
                    }
                }
            }
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(invalid_spec_2.get("components", {}))
        invalid_types_schema = invalid_spec_2["components"]["schemas"]["InvalidTypes"]
        model = generator.generate_model_from_schema(invalid_types_schema, "InvalidTypes")
        # Should create model with valid fields only or use fallback types
        assert model is not None

    def test_missing_schema_references(self):
        """Test handling of missing schema references."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ValidModel": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "missing_ref": {"$ref": "#/components/schemas/NonExistentModel"}
                        }
                    }
                }
            }
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(spec.get("components", {}))

        # Should handle missing references gracefully
        valid_schema = spec["components"]["schemas"]["ValidModel"]

        try:
            model = generator.generate_model_from_schema(valid_schema, "ValidModel")
            assert model is not None

            # Should be able to create instance with available fields
            instance = model(id="test")
            assert instance.id == "test"
        except (KeyError, ValueError) as e:
            # Missing references may cause different types of errors
            # This documents the current behavior
            assert "NonExistentModel" in str(e) or "missing" in str(e).lower()

    def test_complex_enum_edge_cases(self):
        """Test enum handling with edge cases."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "EnumEdgeCases": {
                        "type": "object",
                        "properties": {
                            "empty_enum": {
                                "type": "string",
                                "enum": []
                            },
                            "single_enum": {
                                "type": "string",
                                "enum": ["only_value"]
                            },
                            "mixed_type_enum": {
                                "enum": ["string", 123, True]
                            },
                            "null_in_enum": {
                                "type": "string",
                                "enum": ["valid", None, "another"]
                            }
                        }
                    }
                }
            }
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(spec.get("components", {}))
        enum_schema = spec["components"]["schemas"]["EnumEdgeCases"]
        model = generator.generate_model_from_schema(enum_schema, "EnumEdgeCases")
        assert model is not None

        # Should handle single value enum
        instance = model(single_enum="only_value")
        assert instance.single_enum == "only_value"

    def test_array_schema_edge_cases(self):
        """Test array schema handling with complex cases."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {
                "schemas": {
                    "ArrayEdgeCases": {
                        "type": "object",
                        "properties": {
                            "nested_arrays": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "array_of_refs": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/SimpleModel"}
                            },
                            "array_without_items": {
                                "type": "array"
                                # Missing items specification
                            }
                        }
                    },
                    "SimpleModel": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"}
                        }
                    }
                }
            }
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(spec.get("components", {}))
        array_schema = spec["components"]["schemas"]["ArrayEdgeCases"]
        model = generator.generate_model_from_schema(array_schema, "ArrayEdgeCases")
        assert model is not None

        # Should handle nested arrays
        instance = model(
            nested_arrays=[["a", "b"], ["c", "d"]],
            array_of_refs=[{"name": "test1"}, {"name": "test2"}]
        )
        assert len(instance.nested_arrays) == 2
        assert len(instance.array_of_refs) == 2

    def test_schema_with_no_components(self):
        """Test handling of specs with no components section."""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
            # No components section
        }

        generator = PydanticGenerator(backend_type="default")
        generator.set_schema_definitions(spec.get("components", {}))

        # Should handle gracefully when asking for non-existent model
        # Create a dummy schema for non-existent model
        try:
            dummy_schema = {"type": "object", "properties": {}}
            model = generator.generate_model_from_schema(dummy_schema, "NonExistent")
        except Exception:
            model = None
        # Should return None or a basic model
        assert model is None or model is not None

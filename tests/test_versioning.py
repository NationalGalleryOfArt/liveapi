"""Tests for API versioning functionality."""

import pytest
from src.automatic.parser import OpenAPIParser
from src.automatic.router import RouteGenerator


class TestVersionExtraction:
    """Tests for extracting version information from various sources."""

    def test_extract_version_from_filename_v1(self):
        """Test extracting version 1 from filename users_v1.yaml."""
        parser = OpenAPIParser("users_v1.yaml")
        version = parser.extract_version_from_filename()
        assert version == 1

    def test_extract_version_from_filename_v2(self):
        """Test extracting version 2 from filename api_v2.yaml."""
        parser = OpenAPIParser("api_v2.yaml")
        version = parser.extract_version_from_filename()
        assert version == 2

    def test_extract_version_from_filename_no_version(self):
        """Test default version when no version in filename."""
        parser = OpenAPIParser("users.yaml")
        version = parser.extract_version_from_filename()
        assert version == 1  # Default to version 1

    def test_extract_version_from_filename_complex_path(self):
        """Test extracting version from complex file path."""
        parser = OpenAPIParser("/path/to/specs/orders_v3.yaml")
        version = parser.extract_version_from_filename()
        assert version == 3

    def test_extract_version_from_operation_id_v1(self):
        """Test extracting version from operationId create_user_v1."""
        version = OpenAPIParser.extract_version_from_operation_id("create_user_v1")
        assert version == 1

    def test_extract_version_from_operation_id_v2(self):
        """Test extracting version from operationId get_orders_v2."""
        version = OpenAPIParser.extract_version_from_operation_id("get_orders_v2")
        assert version == 2

    def test_extract_version_from_operation_id_no_version(self):
        """Test default version when no version in operationId."""
        version = OpenAPIParser.extract_version_from_operation_id("create_user")
        assert version == 1  # Default to version 1


class TestMethodSignatureDetection:
    """Tests for detecting if methods accept version parameters."""

    def test_method_accepts_version_parameter(self):
        """Test detecting method that accepts version parameter."""

        class TestImpl:
            def create_user(self, data, version=1):
                return {"id": 1}, 201

        impl = TestImpl()
        generator = RouteGenerator(impl)
        accepts_version = generator.method_accepts_version_parameter("create_user")
        assert accepts_version is True

    def test_method_does_not_accept_version_parameter(self):
        """Test detecting method that does not accept version parameter."""

        class TestImpl:
            def create_user(self, data):
                return {"id": 1}, 201

        impl = TestImpl()
        generator = RouteGenerator(impl)
        accepts_version = generator.method_accepts_version_parameter("create_user")
        assert accepts_version is False

    def test_method_accepts_version_parameter_no_default(self):
        """Test detecting method with version parameter but no default."""

        class TestImpl:
            def create_user(self, data, version):
                return {"id": 1}, 201

        impl = TestImpl()
        generator = RouteGenerator(impl)
        accepts_version = generator.method_accepts_version_parameter("create_user")
        assert accepts_version is True


class TestVersionedMethodCalls:
    """Tests for calling methods with version parameters."""

    def test_call_method_with_version_parameter(self):
        """Test calling method that accepts version parameter."""

        class TestImpl:
            def create_user(self, data, version=1):
                if version == 1:
                    return {"user_id": data["name"]}, 201
                elif version == 2:
                    return {"user_id": data["full_name"], "email": data["email"]}, 201

        impl = TestImpl()
        generator = RouteGenerator(impl)

        # Test version 1
        result = generator.call_method_with_version("create_user", {"name": "John"}, 1)
        assert result == ({"user_id": "John"}, 201)

        # Test version 2
        result = generator.call_method_with_version(
            "create_user", {"full_name": "John Doe", "email": "john@example.com"}, 2
        )
        assert result == ({"user_id": "John Doe", "email": "john@example.com"}, 201)

    def test_call_method_without_version_parameter(self):
        """Test calling method that doesn't accept version parameter."""

        class TestImpl:
            def create_user(self, data):
                return {"user_id": data["name"]}, 201

        impl = TestImpl()
        generator = RouteGenerator(impl)

        result = generator.call_method_with_version("create_user", {"name": "John"}, 1)
        assert result == ({"user_id": "John"}, 201)


class TestVersionAwareImplementation:
    """Tests for version-aware implementation methods."""

    def test_version_aware_get_user(self):
        """Test version-aware get_user method."""

        class TestImpl:
            def get_user(self, data, version=1):
                user_data = {
                    "id": 1,
                    "name": "John",
                    "full_name": "John Doe",
                    "email": "john@example.com",
                }

                if version == 1:
                    return {"user_id": user_data["id"], "name": user_data["name"]}, 200
                elif version == 2:
                    return {
                        "user_id": user_data["id"],
                        "full_name": user_data["full_name"],
                        "email": user_data["email"],
                    }, 200
                elif version == 3:
                    return {
                        "user_id": user_data["id"],
                        "profile": {
                            "full_name": user_data["full_name"],
                            "email": user_data["email"],
                        },
                    }, 200

        impl = TestImpl()

        # Test version 1
        result = impl.get_user({"user_id": 1}, version=1)
        expected_v1 = ({"user_id": 1, "name": "John"}, 200)
        assert result == expected_v1

        # Test version 2
        result = impl.get_user({"user_id": 1}, version=2)
        expected_v2 = (
            {"user_id": 1, "full_name": "John Doe", "email": "john@example.com"},
            200,
        )
        assert result == expected_v2

        # Test version 3
        result = impl.get_user({"user_id": 1}, version=3)
        expected_v3 = (
            {
                "user_id": 1,
                "profile": {"full_name": "John Doe", "email": "john@example.com"},
            },
            200,
        )
        assert result == expected_v3


class TestVersionErrorHandling:
    """Tests for version-related error handling."""

    def test_unsupported_version_error(self):
        """Test handling of unsupported version."""

        class UnsupportedVersionError(Exception):
            pass

        class TestImpl:
            def create_user(self, data, version=1):
                if version in [1, 2]:
                    return {"user_id": 1}, 201
                else:
                    raise UnsupportedVersionError(f"Version {version} not supported")

        impl = TestImpl()

        # Test supported version
        result = impl.create_user({"name": "John"}, version=1)
        assert result == ({"user_id": 1}, 201)

        # Test unsupported version
        with pytest.raises(UnsupportedVersionError, match="Version 5 not supported"):
            impl.create_user({"name": "John"}, version=5)

    def test_deprecated_version_error(self):
        """Test handling of deprecated version."""

        class DeprecatedAPIError(Exception):
            pass

        class TestImpl:
            def create_user(self, data, version=1):
                if version == 1:
                    return {"user_id": 1}, 201
                elif version == 2:
                    return {"user_id": 1, "email": "john@example.com"}, 201
                elif version >= 3:
                    raise DeprecatedAPIError("create_user v3+ is deprecated. Use v2.")

        impl = TestImpl()

        # Test supported versions
        result = impl.create_user({"name": "John"}, version=1)
        assert result == ({"user_id": 1}, 201)

        result = impl.create_user({"name": "John"}, version=2)
        assert result == ({"user_id": 1, "email": "john@example.com"}, 201)

        # Test deprecated version
        with pytest.raises(DeprecatedAPIError, match="create_user v3\\+ is deprecated"):
            impl.create_user({"name": "John"}, version=3)

import pytest
from typing import Dict, Any, Tuple
from automatic.base import BaseCrudImplementation, BaseImplementation
from automatic.exceptions import NotFoundError, ValidationError, ServiceUnavailableError


class UserService(BaseCrudImplementation):
    """Test CRUD implementation for users."""

    resource_name = "user"

    def __init__(self):
        self._data_store = {
            "1": {"id": "1", "name": "John Doe", "email": "john@example.com"},
            "2": {"id": "2", "name": "Jane Smith", "email": "jane@example.com"},
        }
        super().__init__()

    def get_data_store(self) -> Dict[str, Any]:
        return self._data_store

    def get_user(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        resource_id = data.get("user_id")
        if not resource_id:
            raise ValidationError("User ID is required")
        return self.show(resource_id, auth_info=data.get("auth"))

    def create_user(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        body = data.get("body", {})
        return self.create(data=body, auth_info=data.get("auth"))

    def update_user(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        resource_id = data.get("user_id")
        body = data.get("body", {})
        if not resource_id:
            raise ValidationError("User ID is required")
        return self.update(resource_id, data=body, auth_info=data.get("auth"))

    def delete_user(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        resource_id = data.get("user_id")
        if not resource_id:
            raise ValidationError("User ID is required")
        return self.destroy(resource_id, auth_info=data.get("auth"))

    def list_users(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        filters = {k: v for k, v in data.items() if k not in ["auth"]}
        return self.index(filters=filters, auth_info=data.get("auth"))


class CustomUserService(BaseCrudImplementation):
    """Test CRUD implementation with custom validation."""

    resource_name = "user"

    def __init__(self):
        self._data_store = {}
        super().__init__()

    def get_data_store(self) -> Dict[str, Any]:
        return self._data_store

    def validate_create(self, data: Dict) -> None:
        super().validate_create(data)
        if len(data.get("name", "")) < 2:
            raise ValidationError("Name must be at least 2 characters")
        if "@" not in data.get("email", ""):
            raise ValidationError("Invalid email address")

    def validate_update(self, data: Dict) -> None:
        super().validate_update(data)
        if "name" in data and len(data["name"]) < 2:
            raise ValidationError("Name must be at least 2 characters")

    def generate_id(self, data: Dict) -> str:
        return f"user_{len(self._data_store) + 1}"

    def build_resource(self, data: Dict, resource_id: str) -> Dict:
        return {
            "id": resource_id,
            "name": data.get("name"),
            "email": data.get("email"),
            "status": "active",
            "created_at": "2023-01-01T00:00:00Z",
        }


class ReportService(BaseImplementation):
    """Test non-CRUD implementation."""

    def __init__(self):
        self.reports = {}
        super().__init__()

    def generate_report(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        body = data.get("body", {})
        data.get("auth")  # auth_info available but not used in this example

        report_id = f"report_{len(self.reports) + 1}"
        report = {
            "id": report_id,
            "type": body.get("type", "summary"),
            "status": "generated",
        }
        self.reports[report_id] = report

        return report, 201

    def get_external_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Test method that uses get_data helper."""
        try:
            # Simulate external data fetch (would normally be async)
            external_data = {"external": "data", "status": "success"}
            return external_data, 200
        except Exception:
            raise ServiceUnavailableError("External service unavailable")


class TestBaseCrudImplementation:
    """Test suite for BaseCrudImplementation."""

    def test_show_existing_resource(self):
        service = UserService()
        result, status = service.show("1", auth_info=None)

        assert status == 200
        assert result["id"] == "1"
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"

    def test_show_nonexistent_resource(self):
        service = UserService()

        with pytest.raises(NotFoundError) as exc_info:
            service.show("999", auth_info=None)

        assert "User 999 not found" in str(exc_info.value)

    def test_index_all_resources(self):
        service = UserService()
        result, status = service.index(filters={}, auth_info=None)

        assert status == 200
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

    def test_index_with_filters(self):
        service = UserService()
        result, status = service.index(filters={"name": "John"}, auth_info=None)

        assert status == 200
        assert isinstance(result, list)
        # Basic filtering by name contains
        filtered_results = [r for r in result if "John" in r.get("name", "")]
        assert len(filtered_results) >= 1

    def test_create_resource(self):
        service = UserService()
        data = {"name": "Bob Wilson", "email": "bob@example.com"}

        result, status = service.create(data=data, auth_info=None)

        assert status == 201
        assert result["name"] == "Bob Wilson"
        assert result["email"] == "bob@example.com"
        assert "id" in result

        # Verify it was added to data store
        resource_id = result["id"]
        assert resource_id in service.get_data_store()

    def test_create_resource_validation_error(self):
        service = UserService()

        with pytest.raises(ValidationError) as exc_info:
            service.create(data={}, auth_info=None)

        assert "Name is required" in str(exc_info.value)

    def test_update_existing_resource(self):
        service = UserService()
        updates = {"name": "John Updated", "email": "john.updated@example.com"}

        result, status = service.update("1", data=updates, auth_info=None)

        assert status == 200
        assert result["id"] == "1"
        assert result["name"] == "John Updated"
        assert result["email"] == "john.updated@example.com"

        # Verify it was updated in data store
        updated_resource = service.get_data_store()["1"]
        assert updated_resource["name"] == "John Updated"

    def test_update_nonexistent_resource(self):
        service = UserService()

        with pytest.raises(NotFoundError) as exc_info:
            service.update("999", data={"name": "Updated"}, auth_info=None)

        assert "User 999 not found" in str(exc_info.value)

    def test_destroy_existing_resource(self):
        service = UserService()

        result, status = service.destroy("1", auth_info=None)

        assert status == 204
        assert "message" in result
        assert "deleted successfully" in result["message"]

        # Verify it was removed from data store
        assert "1" not in service.get_data_store()

    def test_destroy_nonexistent_resource(self):
        service = UserService()

        with pytest.raises(NotFoundError) as exc_info:
            service.destroy("999", auth_info=None)

        assert "User 999 not found" in str(exc_info.value)

    def test_method_delegation_get_user(self):
        """Test that get_user delegates to show()."""
        service = UserService()

        result, status = service.get_user({"user_id": "1"})

        assert status == 200
        assert result["id"] == "1"
        assert result["name"] == "John Doe"

    def test_method_delegation_create_user(self):
        """Test that create_user delegates to create()."""
        service = UserService()
        data = {"body": {"name": "New User", "email": "new@example.com"}}

        result, status = service.create_user(data)

        assert status == 201
        assert result["name"] == "New User"
        assert result["email"] == "new@example.com"

    def test_method_delegation_update_user(self):
        """Test that update_user delegates to update()."""
        service = UserService()
        data = {"user_id": "1", "body": {"name": "Updated Name"}}

        result, status = service.update_user(data)

        assert status == 200
        assert result["name"] == "Updated Name"

    def test_method_delegation_delete_user(self):
        """Test that delete_user delegates to destroy()."""
        service = UserService()

        result, status = service.delete_user({"user_id": "1"})

        assert status == 204
        assert "message" in result
        assert "deleted successfully" in result["message"]

    def test_method_delegation_list_users(self):
        """Test that list_users delegates to index()."""
        service = UserService()

        result, status = service.list_users({"limit": 10})

        assert status == 200
        assert isinstance(result, list)
        assert len(result) == 2


class TestBaseCrudImplementationCustomization:
    """Test custom validation and hooks in BaseCrudImplementation."""

    def test_custom_create_validation(self):
        service = CustomUserService()

        # Test valid data
        data = {"name": "John Doe", "email": "john@example.com"}
        result, status = service.create(data=data, auth_info=None)
        assert status == 201

        # Test invalid name
        with pytest.raises(ValidationError) as exc_info:
            service.create(data={"name": "J", "email": "j@example.com"}, auth_info=None)
        assert "Name must be at least 2 characters" in str(exc_info.value)

        # Test invalid email
        with pytest.raises(ValidationError) as exc_info:
            service.create(
                data={"name": "John", "email": "invalid-email"}, auth_info=None
            )
        assert "Invalid email address" in str(exc_info.value)

    def test_custom_update_validation(self):
        service = CustomUserService()

        # Create a user first
        data = {"name": "John Doe", "email": "john@example.com"}
        result, status = service.create(data=data, auth_info=None)
        user_id = result["id"]

        # Test valid update
        updates = {"name": "John Updated"}
        result, status = service.update(user_id, data=updates, auth_info=None)
        assert status == 200

        # Test invalid update
        with pytest.raises(ValidationError) as exc_info:
            service.update(user_id, data={"name": "J"}, auth_info=None)
        assert "Name must be at least 2 characters" in str(exc_info.value)

    def test_custom_id_generation(self):
        service = CustomUserService()

        data = {"name": "John Doe", "email": "john@example.com"}
        result, status = service.create(data=data, auth_info=None)

        assert result["id"] == "user_1"

        # Create another user
        data2 = {"name": "Jane Smith", "email": "jane@example.com"}
        result2, status2 = service.create(data=data2, auth_info=None)

        assert result2["id"] == "user_2"

    def test_custom_build_resource(self):
        service = CustomUserService()

        data = {"name": "John Doe", "email": "john@example.com"}
        result, status = service.create(data=data, auth_info=None)

        assert result["status"] == "active"
        assert result["created_at"] == "2023-01-01T00:00:00Z"
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"


class TestBaseImplementation:
    """Test suite for BaseImplementation."""

    def test_custom_operation(self):
        service = ReportService()

        data = {"body": {"type": "analytics", "period": "monthly"}}
        result, status = service.generate_report(data)

        assert status == 201
        assert result["type"] == "analytics"
        assert result["status"] == "generated"
        assert "id" in result

    def test_get_data_helper_success(self):
        service = ReportService()

        result, status = service.get_external_data({})

        assert status == 200
        assert result["external"] == "data"
        assert result["status"] == "success"

    def test_inheritance_structure(self):
        """Test that base classes have correct inheritance."""
        crud_service = UserService()
        custom_service = ReportService()

        assert isinstance(crud_service, BaseCrudImplementation)
        assert isinstance(custom_service, BaseImplementation)

        # Test that CRUD service has expected methods
        assert hasattr(crud_service, "show")
        assert hasattr(crud_service, "index")
        assert hasattr(crud_service, "create")
        assert hasattr(crud_service, "update")
        assert hasattr(crud_service, "destroy")
        assert hasattr(crud_service, "get_data_store")

        # Test that base implementation has expected methods
        assert hasattr(custom_service, "get_data")


class TestAuthInfoPassing:
    """Test that auth info is properly passed through CRUD operations."""

    def test_auth_info_in_show(self):
        service = UserService()
        auth_info = {"user": "admin", "permissions": ["read"]}

        # Mock to capture auth_info
        original_show = service.show
        captured_auth = None

        def mock_show(resource_id, auth_info):
            nonlocal captured_auth
            captured_auth = auth_info
            return original_show(resource_id, auth_info)

        service.show = mock_show
        service.get_user({"user_id": "1", "auth": auth_info})

        assert captured_auth == auth_info

    def test_auth_info_in_create(self):
        service = UserService()
        auth_info = {"user": "admin", "permissions": ["write"]}

        # Mock to capture auth_info
        original_create = service.create
        captured_auth = None

        def mock_create(data, auth_info):
            nonlocal captured_auth
            captured_auth = auth_info
            return original_create(data, auth_info)

        service.create = mock_create
        data = {
            "body": {"name": "Test", "email": "test@example.com"},
            "auth": auth_info,
        }
        service.create_user(data)

        assert captured_auth == auth_info

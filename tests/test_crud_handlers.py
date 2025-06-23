"""Tests for implementation/crud_handlers.py module."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
from typing import Dict, Any, List
from fastapi import HTTPException, Query, Path
from pydantic import BaseModel, ValidationError as PydanticValidationError

from src.liveapi.implementation.crud_handlers import CRUDHandlers, create_crud_router
from src.liveapi.implementation.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
)


# Test model for CRUD operations
class UserModel(BaseModel):
    id: str = None
    name: str
    email: str
    age: int = None
    created_at: str = None
    updated_at: str = None


class TestCRUDHandlers:
    """Test the CRUDHandlers class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handlers = CRUDHandlers(UserModel, "users")

    @pytest.mark.asyncio
    async def test_create_success(self):
        """Test successful resource creation."""
        data = {"name": "John Doe", "email": "john@example.com", "age": 30}

        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="test-id-123")

            result = await self.handlers.create(data)

            assert result["id"] == "test-id-123"
            assert result["name"] == "John Doe"
            assert result["email"] == "john@example.com"
            assert result["age"] == 30
            assert "created_at" in result
            assert "updated_at" in result
            assert result["created_at"] == result["updated_at"]

    @pytest.mark.asyncio
    async def test_create_with_existing_id(self):
        """Test creating resource with provided ID."""
        data = {"id": "custom-id", "name": "Jane Doe", "email": "jane@example.com"}

        result = await self.handlers.create(data)

        assert result["id"] == "custom-id"
        assert result["name"] == "Jane Doe"
        assert result["email"] == "jane@example.com"

    @pytest.mark.asyncio
    async def test_create_conflict(self):
        """Test creating resource with duplicate ID."""
        data = {"id": "duplicate-id", "name": "User 1", "email": "user1@example.com"}

        # Create first user
        await self.handlers.create(data)

        # Try to create another with same ID
        data2 = {"id": "duplicate-id", "name": "User 2", "email": "user2@example.com"}

        with pytest.raises(ConflictError) as exc_info:
            await self.handlers.create(data2)

        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_validation_error(self):
        """Test creating resource with invalid data."""
        data = {"name": "John", "email": "invalid-email", "age": "not-a-number"}

        with pytest.raises(ValidationError) as exc_info:
            await self.handlers.create(data)

        assert "Invalid data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_read_success(self):
        """Test successful resource reading."""
        # Create a resource first
        data = {"id": "read-test", "name": "Test User", "email": "test@example.com"}
        await self.handlers.create(data)

        result = await self.handlers.read("read-test")

        assert result["id"] == "read-test"
        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_read_not_found(self):
        """Test reading non-existent resource."""
        with pytest.raises(NotFoundError) as exc_info:
            await self.handlers.read("non-existent-id")

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_full_success(self):
        """Test successful full update (PUT)."""
        # Create a resource first
        data = {
            "id": "update-test",
            "name": "Original",
            "email": "original@example.com",
            "age": 25,
        }
        created = await self.handlers.create(data)
        original_created_at = created["created_at"]

        # Update the resource
        update_data = {"name": "Updated", "email": "updated@example.com", "age": 30}
        result = await self.handlers.update("update-test", update_data, partial=False)

        assert result["id"] == "update-test"
        assert result["name"] == "Updated"
        assert result["email"] == "updated@example.com"
        assert result["age"] == 30
        assert result["created_at"] == original_created_at
        assert result["updated_at"] != original_created_at

    @pytest.mark.asyncio
    async def test_update_partial_success(self):
        """Test successful partial update (PATCH)."""
        # Create a resource first
        data = {
            "id": "patch-test",
            "name": "Original",
            "email": "original@example.com",
            "age": 25,
        }
        created = await self.handlers.create(data)

        # Partial update
        update_data = {"name": "Patched"}
        result = await self.handlers.update("patch-test", update_data, partial=True)

        assert result["id"] == "patch-test"
        assert result["name"] == "Patched"
        assert result["email"] == "original@example.com"  # Should remain unchanged
        assert result["age"] == 25  # Should remain unchanged

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        """Test updating non-existent resource."""
        update_data = {"name": "Updated"}

        with pytest.raises(NotFoundError) as exc_info:
            await self.handlers.update("non-existent", update_data)

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_validation_error(self):
        """Test updating with invalid data."""
        # Create a resource first
        data = {"id": "validation-test", "name": "Test", "email": "test@example.com"}
        await self.handlers.create(data)

        # Try to update with invalid data
        update_data = {"email": "invalid-email", "age": "not-a-number"}

        with pytest.raises(ValidationError) as exc_info:
            await self.handlers.update("validation-test", update_data)

        assert "Invalid data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test successful resource deletion."""
        # Create a resource first
        data = {"id": "delete-test", "name": "To Delete", "email": "delete@example.com"}
        await self.handlers.create(data)

        # Verify it exists
        result = await self.handlers.read("delete-test")
        assert result["id"] == "delete-test"

        # Delete it
        await self.handlers.delete("delete-test")

        # Verify it's gone
        with pytest.raises(NotFoundError):
            await self.handlers.read("delete-test")

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Test deleting non-existent resource."""
        with pytest.raises(NotFoundError) as exc_info:
            await self.handlers.delete("non-existent")

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_empty(self):
        """Test listing when no resources exist."""
        result = await self.handlers.list(limit=100, offset=0)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_with_resources(self):
        """Test listing with multiple resources."""
        # Create several resources
        for i in range(5):
            data = {
                "id": f"user-{i}",
                "name": f"User {i}",
                "email": f"user{i}@example.com",
            }
            await self.handlers.create(data)

        result = await self.handlers.list(limit=100, offset=0)

        assert len(result) == 5
        assert all(user["name"].startswith("User") for user in result)

    @pytest.mark.asyncio
    async def test_list_with_limit_offset(self):
        """Test listing with limit and offset."""
        # Create 10 resources
        for i in range(10):
            data = {
                "id": f"user-{i}",
                "name": f"User {i}",
                "email": f"user{i}@example.com",
            }
            await self.handlers.create(data)

        # Test limit
        result = await self.handlers.list(limit=3, offset=0)
        assert len(result) == 3

        # Test offset
        result = await self.handlers.list(limit=3, offset=3)
        assert len(result) == 3

        # Test limit + offset beyond available
        result = await self.handlers.list(limit=5, offset=8)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_with_filters(self):
        """Test listing with custom filters."""
        # Create resources with different attributes
        await self.handlers.create(
            {"id": "user-1", "name": "Alice", "email": "alice@example.com", "age": 25}
        )
        await self.handlers.create(
            {"id": "user-2", "name": "Bob", "email": "bob@example.com", "age": 30}
        )
        await self.handlers.create(
            {
                "id": "user-3",
                "name": "Charlie",
                "email": "charlie@example.com",
                "age": 35,
            }
        )

        # Test filtering (manual since Query parameters can't be passed directly)
        all_results = await self.handlers.list(limit=100, offset=0)
        alice_users = [r for r in all_results if r.get("name") == "Alice"]
        assert len(alice_users) == 1
        assert alice_users[0]["name"] == "Alice"

    def test_apply_filters_exact_match(self):
        """Test _apply_filters with exact match."""
        resources = [
            {"id": "1", "name": "Alice", "age": 25},
            {"id": "2", "name": "Bob", "age": 30},
            {"id": "3", "name": "Alice", "age": 35},
        ]

        filters = {"name": "Alice"}
        result = self.handlers._apply_filters(resources, filters)

        assert len(result) == 2
        assert all(r["name"] == "Alice" for r in result)

    def test_apply_filters_gte(self):
        """Test _apply_filters with greater than or equal filter."""
        resources = [
            {"id": "1", "name": "Alice", "age": 25},
            {"id": "2", "name": "Bob", "age": 30},
            {"id": "3", "name": "Charlie", "age": 35},
        ]

        filters = {"age__gte": 30}
        result = self.handlers._apply_filters(resources, filters)

        assert len(result) == 2
        assert all(r["age"] >= 30 for r in result)

    def test_apply_filters_lte(self):
        """Test _apply_filters with less than or equal filter."""
        resources = [
            {"id": "1", "name": "Alice", "age": 25},
            {"id": "2", "name": "Bob", "age": 30},
            {"id": "3", "name": "Charlie", "age": 35},
        ]

        filters = {"age__lte": 30}
        result = self.handlers._apply_filters(resources, filters)

        assert len(result) == 2
        assert all(r["age"] <= 30 for r in result)

    def test_apply_filters_contains(self):
        """Test _apply_filters with contains filter."""
        resources = [
            {"id": "1", "name": "Alice", "email": "alice@gmail.com"},
            {"id": "2", "name": "Bob", "email": "bob@yahoo.com"},
            {"id": "3", "name": "Charlie", "email": "charlie@gmail.com"},
        ]

        filters = {"email__contains": "gmail"}
        result = self.handlers._apply_filters(resources, filters)

        assert len(result) == 2
        assert all("gmail" in r["email"] for r in result)

    def test_apply_filters_no_filters(self):
        """Test _apply_filters with no filters."""
        resources = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]

        result = self.handlers._apply_filters(resources, {})

        assert result == resources

    def test_apply_filters_skip_pagination(self):
        """Test _apply_filters skips pagination parameters."""
        resources = [
            {"id": "1", "name": "Alice", "limit": 10, "offset": 0},
            {"id": "2", "name": "Bob", "limit": 5, "offset": 10},
        ]

        filters = {"limit": 100, "offset": 50}  # These should be ignored
        result = self.handlers._apply_filters(resources, filters)

        assert len(result) == 2  # All resources should be returned


class TestCreateCrudRouter:
    """Test the create_crud_router function."""

    def test_create_router_structure(self):
        """Test that router is created with correct structure."""
        router = create_crud_router("users", UserModel)

        # Check that router is created
        assert router is not None

        # Check routes are added (this is basic structure test)
        # More detailed endpoint testing would require FastAPI TestClient

    @patch("fastapi.APIRouter")
    def test_create_router_handlers_initialization(self, mock_router_class):
        """Test that handlers are properly initialized."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router

        router = create_crud_router("products", UserModel)

        # Verify APIRouter was called
        mock_router_class.assert_called_once()

        # Verify decorator methods were called for each endpoint
        assert mock_router.post.called
        assert mock_router.get.called
        assert mock_router.put.called
        assert mock_router.patch.called
        assert mock_router.delete.called

    def test_router_endpoint_paths(self):
        """Test that router creates correct endpoint paths."""
        with patch("fastapi.APIRouter") as mock_router_class:
            mock_router = Mock()
            mock_router_class.return_value = mock_router

            create_crud_router("items", UserModel)

            # Check POST endpoint
            mock_router.post.assert_called()
            post_call = mock_router.post.call_args
            assert "/items" in post_call[0][0]

            # Check GET endpoints
            get_calls = [call[0][0] for call in mock_router.get.call_args_list]
            assert any("/items/{resource_id}" in path for path in get_calls)
            assert any("/items" in path for path in get_calls)

            # Check PUT endpoint
            mock_router.put.assert_called()
            put_call = mock_router.put.call_args
            assert "/items/{resource_id}" in put_call[0][0]

            # Check PATCH endpoint
            mock_router.patch.assert_called()
            patch_call = mock_router.patch.call_args
            assert "/items/{resource_id}" in patch_call[0][0]

            # Check DELETE endpoint
            mock_router.delete.assert_called()
            delete_call = mock_router.delete.call_args
            assert "/items/{resource_id}" in delete_call[0][0]

    def test_router_response_models(self):
        """Test that router endpoints have correct response models."""
        with patch("fastapi.APIRouter") as mock_router_class:
            mock_router = Mock()
            mock_router_class.return_value = mock_router

            create_crud_router("users", UserModel)

            # Check that response_model parameter is used
            post_call = mock_router.post.call_args
            assert "response_model" in post_call[1]
            assert post_call[1]["response_model"] == UserModel

            get_calls = mock_router.get.call_args_list
            # Check individual resource GET has response model
            individual_get = [
                call for call in get_calls if "resource_id" in call[0][0]
            ][0]
            assert "response_model" in individual_get[1]
            assert individual_get[1]["response_model"] == UserModel

    def test_router_status_codes(self):
        """Test that router endpoints have correct status codes."""
        with patch("fastapi.APIRouter") as mock_router_class:
            mock_router = Mock()
            mock_router_class.return_value = mock_router

            create_crud_router("users", UserModel)

            # Check DELETE endpoint has 204 status code
            delete_call = mock_router.delete.call_args
            assert "status_code" in delete_call[1]
            assert delete_call[1]["status_code"] == 204


class TestCRUDHandlersIntegration:
    """Integration tests for CRUD handlers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handlers = CRUDHandlers(UserModel, "users")

    @pytest.mark.asyncio
    async def test_full_crud_workflow(self):
        """Test complete CRUD workflow."""
        # Create
        create_data = {
            "name": "Integration Test",
            "email": "integration@example.com",
            "age": 28,
        }
        created = await self.handlers.create(create_data)
        user_id = created["id"]

        # Read
        read_result = await self.handlers.read(user_id)
        assert read_result["name"] == "Integration Test"

        # Update
        update_data = {
            "name": "Updated Integration",
            "email": "updated@example.com",
            "age": 30,
        }
        updated = await self.handlers.update(user_id, update_data)
        assert updated["name"] == "Updated Integration"
        assert updated["age"] == 30

        # List (should contain our user)
        list_result = await self.handlers.list(limit=100, offset=0)
        assert len(list_result) == 1
        assert list_result[0]["id"] == user_id

        # Delete
        await self.handlers.delete(user_id)

        # Verify deletion
        with pytest.raises(NotFoundError):
            await self.handlers.read(user_id)

        # List should be empty
        list_result = await self.handlers.list(limit=100, offset=0)
        assert len(list_result) == 0

    @pytest.mark.asyncio
    async def test_multiple_resources_management(self):
        """Test managing multiple resources."""
        # Create multiple users
        users_data = [
            {"name": "User 1", "email": "user1@example.com", "age": 20},
            {"name": "User 2", "email": "user2@example.com", "age": 25},
            {"name": "User 3", "email": "user3@example.com", "age": 30},
        ]

        created_ids = []
        for data in users_data:
            created = await self.handlers.create(data)
            created_ids.append(created["id"])

        # List all
        all_users = await self.handlers.list(limit=100, offset=0)
        assert len(all_users) == 3

        # Test filtering (manual since Query parameters don't work in direct calls)
        young_users = [u for u in all_users if u.get("age", 0) <= 25]
        assert len(young_users) == 2

        # Delete one user
        await self.handlers.delete(created_ids[1])

        # Verify count
        remaining_users = await self.handlers.list(limit=100, offset=0)
        assert len(remaining_users) == 2

        # Verify the correct user was deleted
        remaining_ids = [user["id"] for user in remaining_users]
        assert created_ids[1] not in remaining_ids
        assert created_ids[0] in remaining_ids
        assert created_ids[2] in remaining_ids

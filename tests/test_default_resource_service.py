"""Unit and integration tests for the DefaultResourceService."""

import pytest
from typing import Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from src.liveapi.implementation.default_resource_service import (
    DefaultResourceService,
    create_resource_router,
)
from src.liveapi.implementation.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
)


class UserModel(BaseModel):
    """Pydantic model for testing."""

    id: str | None = None
    name: str = Field(min_length=2)
    email: str
    created_at: str | None = None
    updated_at: str | None = None


@pytest.fixture
def user_data() -> Dict[str, Any]:
    """Return sample user data."""
    return {"name": "Test User", "email": "test@example.com"}


class TestDefaultResourceService:
    """Test the DefaultResourceService class."""

    @pytest.fixture(autouse=True)
    def set_up(self):
        """Set up test fixtures."""
        self.service = DefaultResourceService(UserModel, "users")

    @pytest.mark.asyncio
    async def test_create_success(self, user_data: Dict[str, Any]):
        """Test successful resource creation."""
        created = await self.service.create(user_data)
        assert "id" in created
        assert created["name"] == user_data["name"]
        assert "created_at" in created
        assert "updated_at" in created

    @pytest.mark.asyncio
    async def test_create_with_existing_id(self, user_data: Dict[str, Any]):
        """Test resource creation with a provided ID."""
        user_data["id"] = "custom-id"
        created = await self.service.create(user_data)
        assert created["id"] == "custom-id"

    @pytest.mark.asyncio
    async def test_create_conflict(self, user_data: Dict[str, Any]):
        """Test that creating a resource with a duplicate ID raises ConflictError."""
        user_data["id"] = "conflict-id"
        await self.service.create(user_data)
        with pytest.raises(ConflictError):
            await self.service.create(user_data)

    @pytest.mark.asyncio
    async def test_create_validation_error(self):
        """Test that invalid data raises ValidationError on create."""
        with pytest.raises(ValidationError):
            await self.service.create({"name": "T"})  # Name too short

    @pytest.mark.asyncio
    async def test_read_success(self, user_data: Dict[str, Any]):
        """Test successful resource read."""
        created = await self.service.create(user_data)
        retrieved = await self.service.read(created["id"])
        assert retrieved == created

    @pytest.mark.asyncio
    async def test_read_not_found(self):
        """Test that reading a non-existent resource raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await self.service.read("non-existent-id")

    @pytest.mark.asyncio
    async def test_update_full_success(self, user_data: Dict[str, Any]):
        """Test successful full resource update (PUT)."""
        created = await self.service.create(user_data)
        update_data = {"name": "Updated Name", "email": "updated@example.com"}
        updated = await self.service.update(created["id"], update_data)
        assert updated["name"] == "Updated Name"
        assert updated["id"] == created["id"]
        assert updated["created_at"] == created["created_at"]
        assert updated["updated_at"] > created["updated_at"]

    @pytest.mark.asyncio
    async def test_update_partial_success(self, user_data: Dict[str, Any]):
        """Test successful partial resource update (PATCH)."""
        created = await self.service.create(user_data)
        update_data = {"name": "Patched Name"}
        updated = await self.service.update(created["id"], update_data, partial=True)
        assert updated["name"] == "Patched Name"
        assert updated["email"] == user_data["email"]  # Should not change
        assert updated["updated_at"] > created["updated_at"]

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        """Test that updating a non-existent resource raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await self.service.update("non-existent-id", {"name": "some name"})

    @pytest.mark.asyncio
    async def test_update_validation_error(self, user_data: Dict[str, Any]):
        """Test that invalid data raises ValidationError on update."""
        created = await self.service.create(user_data)
        with pytest.raises(ValidationError):
            await self.service.update(created["id"], {"name": "T"})

    @pytest.mark.asyncio
    async def test_delete_success(self, user_data: Dict[str, Any]):
        """Test successful resource deletion."""
        created = await self.service.create(user_data)
        await self.service.delete(created["id"])
        with pytest.raises(NotFoundError):
            await self.service.read(created["id"])

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        """Test that deleting a non-existent resource raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await self.service.delete("non-existent-id")

    @pytest.mark.asyncio
    async def test_list_empty(self):
        """Test listing resources when none exist."""
        resources = await self.service.list()
        assert resources == []

    @pytest.mark.asyncio
    async def test_list_with_resources(self, user_data: Dict[str, Any]):
        """Test listing resources."""
        await self.service.create(user_data)
        await self.service.create({"name": "User 2", "email": "user2@example.com"})
        resources = await self.service.list()
        assert len(resources) == 2

    @pytest.mark.asyncio
    async def test_list_with_limit_offset(self, user_data: Dict[str, Any]):
        """Test listing with limit and offset."""
        for i in range(5):
            await self.service.create(
                {"name": f"User {i}", "email": f"user{i}@example.com"}
            )

        # Test limit
        resources = await self.service.list(limit=2)
        assert len(resources) == 2

        # Test offset
        resources = await self.service.list(limit=2, offset=2)
        assert len(resources) == 2
        assert resources[0]["name"] == "User 2"

    @pytest.mark.asyncio
    async def test_apply_filters_no_filters(self):
        """Test that _apply_filters returns all resources if no filters are provided."""
        all_resources = [{"id": "1", "value": 10}, {"id": "2", "value": 20}]
        self.service._storage = {r["id"]: r for r in all_resources}
        filtered = self.service._apply_filters(all_resources, {})
        assert filtered == all_resources

    @pytest.mark.asyncio
    async def test_apply_filters_exact_match(self):
        """Test exact match filtering."""
        all_resources = [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]
        self.service._storage = {r["id"]: r for r in all_resources}
        filtered = self.service._apply_filters(all_resources, {"name": "A"})
        assert len(filtered) == 1
        assert filtered[0]["name"] == "A"

    @pytest.mark.asyncio
    async def test_apply_filters_gte(self):
        """Test greater than or equal filtering."""
        all_resources = [{"id": "1", "value": 10}, {"id": "2", "value": 20}]
        self.service._storage = {r["id"]: r for r in all_resources}
        filtered = self.service._apply_filters(all_resources, {"value__gte": 15})
        assert len(filtered) == 1
        assert filtered[0]["value"] == 20

    @pytest.mark.asyncio
    async def test_apply_filters_lte(self):
        """Test less than or equal filtering."""
        all_resources = [{"id": "1", "value": 10}, {"id": "2", "value": 20}]
        self.service._storage = {r["id"]: r for r in all_resources}
        filtered = self.service._apply_filters(all_resources, {"value__lte": 15})
        assert len(filtered) == 1
        assert filtered[0]["value"] == 10

    @pytest.mark.asyncio
    async def test_apply_filters_contains(self):
        """Test 'contains' filtering for strings."""
        all_resources = [{"id": "1", "name": "Test"}, {"id": "2", "name": "Another"}]
        self.service._storage = {r["id"]: r for r in all_resources}
        filtered = self.service._apply_filters(all_resources, {"name__contains": "est"})
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Test"

    @pytest.mark.asyncio
    async def test_apply_filters_skip_pagination(self):
        """Test that pagination parameters are skipped during filtering."""
        all_resources = [{"id": "1", "name": "A"}]
        self.service._storage = {r["id"]: r for r in all_resources}
        filtered = self.service._apply_filters(all_resources, {"limit": 1, "offset": 0})
        assert len(filtered) == 1


class TestDefaultResourceServiceIntegration:
    """Integration tests for the DefaultResourceService."""

    @pytest.fixture(autouse=True)
    def set_up(self):
        """Set up test fixtures."""
        self.service = DefaultResourceService(UserModel, "users")

    @pytest.mark.asyncio
    async def test_full_crud_workflow(self, user_data: Dict[str, Any]):
        """Test a full create-read-update-delete workflow."""
        # Create
        created = await self.service.create(user_data)
        resource_id = created["id"]
        assert created["name"] == "Test User"

        # Read
        read = await self.service.read(resource_id)
        assert read == created

        # Update
        updated = await self.service.update(
            resource_id, {"name": "Updated", "email": "updated@example.com"}
        )
        assert updated["name"] == "Updated"
        assert updated["email"] == "updated@example.com"

        # List
        resources = await self.service.list()
        assert len(resources) == 1

        # Delete
        await self.service.delete(resource_id)
        with pytest.raises(NotFoundError):
            await self.service.read(resource_id)

    @pytest.mark.asyncio
    async def test_multiple_resources_management(self):
        """Test managing multiple resources."""
        # Create multiple resources
        user1 = await self.service.create({"name": "User 1", "email": "u1@test.com"})
        user2 = await self.service.create({"name": "User 2", "email": "u2@test.com"})

        # List and check count
        resources = await self.service.list()
        assert len(resources) == 2

        # Delete one
        await self.service.delete(user1["id"])

        # List again and check
        resources = await self.service.list()
        assert len(resources) == 1
        assert resources[0]["id"] == user2["id"]


class TestCreateResourceRouter:
    """Test the create_resource_router factory function."""

    def test_create_router_handlers_initialization(self):
        """Test that the router is created and handlers are initialized."""
        router = create_resource_router("users", UserModel)
        assert router is not None
        # This is a bit of a white-box test, but it's a good sanity check
        # In a real app, you'd test the endpoints, not the internals.
        assert len(router.routes) > 0

    def test_router_endpoints(self, user_data: Dict[str, Any]):
        """Test the created router's endpoints with a TestClient."""
        app = FastAPI()

        @app.exception_handler(NotFoundError)
        async def not_found_exception_handler(request, exc):
            return JSONResponse(status_code=404, content={"detail": str(exc)})

        router = create_resource_router("users", UserModel)
        app.include_router(router)
        client = TestClient(app)

        # Test POST (Create)
        response = client.post("/users", json=user_data)
        assert response.status_code == 200  # create_resource_router uses 200
        created_user = response.json()
        assert "id" in created_user
        user_id = created_user["id"]

        # Test GET (Read)
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["name"] == user_data["name"]

        # Test PUT (Update)
        update_data = {"name": "Updated User", "email": "updated@test.com"}
        response = client.put(f"/users/{user_id}", json=update_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated User"

        # Test PATCH (Partial Update)
        patch_data = {"name": "Patched User"}
        response = client.patch(f"/users/{user_id}", json=patch_data)
        assert response.status_code == 200
        assert response.json()["name"] == "Patched User"
        assert (
            response.json()["email"] == "updated@test.com"
        )  # email should be preserved

        # Test GET (List)
        response = client.get("/users")
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Test DELETE
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 404

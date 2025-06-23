"""Standard CRUD+ handlers for LiveAPI."""

from typing import Dict, Any, List, Optional, Type
from fastapi import HTTPException, Query, Path
from pydantic import BaseModel
from .exceptions import NotFoundError, ValidationError, ConflictError


class CRUDHandlers:
    """Standard handlers for CRUD+ operations.

    This class provides reusable handlers for the standard CRUD+ interface:
    - Create: POST /resources
    - Read: GET /resources/{id}
    - Update: PUT/PATCH /resources/{id}
    - Delete: DELETE /resources/{id}
    - List: GET /resources
    - Search: GET /resources with query parameters
    """

    def __init__(self, model: Type[BaseModel], resource_name: str):
        """Initialize CRUD handlers.

        Args:
            model: Pydantic model for the resource
            resource_name: Name of the resource (e.g., "users")
        """
        self.resource_name = resource_name
        self.model = model
        self._storage: Dict[str, Dict[str, Any]] = {}  # In-memory storage

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource.

        Args:
            data: Resource data validated by Pydantic model

        Returns:
            Created resource with generated ID

        Raises:
            ConflictError: If resource with same ID already exists
            ValidationError: If data validation fails
        """
        # Validate data with Pydantic model
        try:
            validated = self.model(**data)
            resource_data = validated.model_dump()
        except Exception as e:
            raise ValidationError(f"Invalid data: {str(e)}")

        # Get or generate ID
        resource_id = resource_data.get("id")
        if not resource_id:
            # Generate ID if not provided
            import uuid

            resource_id = str(uuid.uuid4())
            resource_data["id"] = resource_id

        # Check for conflicts
        if resource_id in self._storage:
            raise ConflictError(
                f"{self.resource_name} with ID {resource_id} already exists"
            )

        # Add timestamps
        from datetime import datetime, UTC

        now = datetime.now(UTC).isoformat()
        resource_data["created_at"] = now
        resource_data["updated_at"] = now

        # Store the resource
        self._storage[resource_id] = resource_data

        return resource_data

    async def read(self, resource_id: str) -> Dict[str, Any]:
        """Read a single resource by ID.

        Args:
            resource_id: The ID of the resource

        Returns:
            The resource data

        Raises:
            NotFoundError: If resource doesn't exist
        """
        if resource_id not in self._storage:
            raise NotFoundError(f"{self.resource_name} with ID {resource_id} not found")

        return self._storage[resource_id]

    async def update(
        self, resource_id: str, data: Dict[str, Any], partial: bool = False
    ) -> Dict[str, Any]:
        """Update an existing resource.

        Args:
            resource_id: The ID of the resource
            data: Updated resource data
            partial: If True, allows partial updates (PATCH)

        Returns:
            The updated resource

        Raises:
            NotFoundError: If resource doesn't exist
            ValidationError: If data validation fails
        """
        if resource_id not in self._storage:
            raise NotFoundError(f"{self.resource_name} with ID {resource_id} not found")

        existing = self._storage[resource_id].copy()

        if partial:
            # PATCH: Merge with existing data
            existing.update(data)
            update_data = existing
        else:
            # PUT: Replace entirely
            update_data = data
            # Preserve system fields
            update_data["id"] = resource_id
            update_data["created_at"] = existing.get("created_at")

        # Validate updated data
        try:
            validated = self.model(**update_data)
            resource_data = validated.model_dump()
        except Exception as e:
            raise ValidationError(f"Invalid data: {str(e)}")

        # Update timestamp
        from datetime import datetime, UTC

        resource_data["updated_at"] = datetime.now(UTC).isoformat()

        # Store updated resource
        self._storage[resource_id] = resource_data

        return resource_data

    async def delete(self, resource_id: str) -> None:
        """Delete a resource.

        Args:
            resource_id: The ID of the resource

        Raises:
            NotFoundError: If resource doesn't exist
        """
        if resource_id not in self._storage:
            raise NotFoundError(f"{self.resource_name} with ID {resource_id} not found")

        del self._storage[resource_id]

    async def list(
        self,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        **filters: Any,
    ) -> List[Dict[str, Any]]:
        """List resources (simplified - no pagination).

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            **filters: Additional filter parameters

        Returns:
            Simple list of resources
        """
        # Get all resources
        all_resources = list(self._storage.values())

        # Apply filters
        filtered = self._apply_filters(all_resources, filters)

        # Apply simple limit/offset (no pagination wrapper)
        return filtered[offset : offset + limit]

    def _apply_filters(
        self, resources: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to resource list.

        Args:
            resources: List of resources to filter
            filters: Filter parameters

        Returns:
            Filtered list of resources
        """
        if not filters:
            return resources

        filtered = []
        for resource in resources:
            match = True
            for key, value in filters.items():
                # Skip pagination parameters
                if key in ("limit", "offset"):
                    continue

                # Handle different filter types
                if key.endswith("__gte"):
                    # Greater than or equal
                    field = key[:-5]
                    if field in resource and resource[field] < value:
                        match = False
                        break
                elif key.endswith("__lte"):
                    # Less than or equal
                    field = key[:-5]
                    if field in resource and resource[field] > value:
                        match = False
                        break
                elif key.endswith("__contains"):
                    # Contains (for strings)
                    field = key[:-10]
                    if field in resource and value not in str(resource[field]):
                        match = False
                        break
                else:
                    # Exact match
                    if key in resource and resource[key] != value:
                        match = False
                        break

            if match:
                filtered.append(resource)

        return filtered


def create_crud_router(resource_name: str, model: Type[BaseModel]):
    """Create a FastAPI router with CRUD+ endpoints for a resource.

    Args:
        resource_name: Name of the resource (e.g., "users")
        model: Pydantic model for the resource

    Returns:
        FastAPI APIRouter with CRUD+ endpoints
    """
    from fastapi import APIRouter

    router = APIRouter()
    handlers = CRUDHandlers(model, resource_name)

    # Create
    @router.post(f"/{resource_name}", response_model=model)
    async def create_resource(data: model):
        return await handlers.create(data.model_dump())

    # Read
    @router.get(f"/{resource_name}/{{resource_id}}", response_model=model)
    async def read_resource(resource_id: str = Path(...)):
        return await handlers.read(resource_id)

    # Update (PUT)
    @router.put(f"/{resource_name}/{{resource_id}}", response_model=model)
    async def update_resource(resource_id: str = Path(...), data: model = ...):
        return await handlers.update(resource_id, data.model_dump(), partial=False)

    # Update (PATCH)
    @router.patch(f"/{resource_name}/{{resource_id}}", response_model=model)
    async def patch_resource(resource_id: str = Path(...), data: Dict[str, Any] = ...):
        return await handlers.update(resource_id, data, partial=True)

    # Delete
    @router.delete(f"/{resource_name}/{{resource_id}}", status_code=204)
    async def delete_resource(resource_id: str = Path(...)):
        await handlers.delete(resource_id)
        return None

    # List
    @router.get(f"/{resource_name}")
    async def list_resources(
        limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)
    ):
        return await handlers.list(limit=limit, offset=offset)

    return router

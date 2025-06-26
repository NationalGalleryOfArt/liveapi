"""Base SQLModel resource with hook-based customization system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type
from datetime import datetime, timezone
import uuid

from sqlmodel import SQLModel, Session, select, and_
from sqlalchemy.exc import IntegrityError

from .exceptions import NotFoundError, ValidationError, ConflictError


class BaseSQLModelResource(ABC):
    """Abstract base class for database-backed resource services using SQLModel.
    
    This class contains the core CRUD logic and defines hook methods that
    subclasses can override to customize behavior without reimplementing
    the entire CRUD operations.
    """

    def __init__(self, model: Type[SQLModel], resource_name: str, session: Session):
        """Initialize the SQL resource service.

        Args:
            model: SQLModel class for the resource
            resource_name: Name of the resource (e.g., "users")
            session: The database session to use for operations.
        """
        self.resource_name = resource_name
        self.model = model
        self.session = session

    # --- Data Transformation Hooks ---
    
    def to_dto(self, db_resource: SQLModel) -> Dict[str, Any]:
        """Transform database model to API-friendly dictionary (DTO).
        
        Default implementation returns the model as-is using model_dump.
        Override this to customize the API response format.
        
        Args:
            db_resource: The database model instance
            
        Returns:
            Dictionary representation for API response
        """
        return db_resource.model_dump(mode="json")
    
    def from_api(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform incoming API data to database model format.
        
        Default implementation returns the data as-is.
        Override this to transform API input to match database schema.
        
        Args:
            data: Incoming API data
            
        Returns:
            Dictionary suitable for database model
        """
        return data
    
    # --- Lifecycle Hooks ---
    
    async def before_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before a new resource is created.
        
        Default implementation returns data unchanged.
        Override to add validation, set defaults, or modify data.
        
        Args:
            data: Resource data to be created
            
        Returns:
            Modified resource data
        """
        return data
    
    async def after_create(self, resource: SQLModel) -> None:
        """Called after a new resource is created.
        
        Default implementation does nothing.
        Override to trigger side effects like sending notifications.
        
        Args:
            resource: The created database model instance
        """
        pass
    
    async def before_update(self, resource_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Called before a resource is updated.
        
        Default implementation returns data unchanged.
        Override to add validation or modify update data.
        
        Args:
            resource_id: ID of the resource being updated
            data: Update data
            
        Returns:
            Modified update data
        """
        return data
    
    async def after_update(self, resource: SQLModel) -> None:
        """Called after a resource is updated.
        
        Default implementation does nothing.
        Override to trigger side effects like cache invalidation.
        
        Args:
            resource: The updated database model instance
        """
        pass
    
    async def before_delete(self, resource_id: Any) -> None:
        """Called before a resource is deleted.
        
        Default implementation does nothing.
        Override to add validation or prevent deletion.
        
        Args:
            resource_id: ID of the resource being deleted
        """
        pass
    
    async def after_delete(self, resource_id: Any) -> None:
        """Called after a resource is deleted.
        
        Default implementation does nothing.
        Override to trigger cleanup or cascading deletes.
        
        Args:
            resource_id: ID of the deleted resource
        """
        pass
    
    # --- Query Hooks ---
    
    def build_list_query(self, query: select, filters: Dict[str, Any]) -> select:
        """Customize the query used to list resources.
        
        Default implementation applies basic filters.
        Override to add joins, custom filters, or ordering.
        
        Args:
            query: Base SQLModel select query
            filters: Filter parameters from API
            
        Returns:
            Modified query
        """
        return self._apply_filters(query, filters)

    # --- Core CRUD Implementation ---

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource in the database.

        Args:
            data: Resource data validated by SQLModel

        Returns:
            Created resource with generated ID

        Raises:
            ConflictError: If resource with same ID already exists
            ValidationError: If data validation fails
        """
        try:
            # Transform API data to database format
            resource_data = self.from_api(data.copy())
            
            # Call before_create hook
            resource_data = await self.before_create(resource_data)

            # Get or generate ID
            resource_id = resource_data.get("id")
            if not resource_id:
                resource_id = str(uuid.uuid4())
                resource_data["id"] = resource_id

            # Add timestamps if the model supports them
            now = datetime.now(timezone.utc)
            if hasattr(self.model, "created_at"):
                resource_data["created_at"] = now
            if hasattr(self.model, "updated_at"):
                resource_data["updated_at"] = now

            # Create and validate the model instance
            db_resource = self.model(**resource_data)

            # Save to database
            # Check for existing resource with same ID
            existing = self.session.get(self.model, resource_id)
            if existing:
                raise ConflictError(
                    f"{self.resource_name} with ID {resource_id} already exists"
                )

            self.session.add(db_resource)
            self.session.commit()
            self.session.refresh(db_resource)
            
            # Call after_create hook
            await self.after_create(db_resource)

            # Transform to DTO for return
            return self.to_dto(db_resource)

        except IntegrityError as e:
            self.session.rollback()
            raise ConflictError(f"Database constraint violation: {str(e)}")
        except Exception as e:
            self.session.rollback()
            if isinstance(e, (ConflictError, ValidationError)):
                raise
            raise ValidationError(f"Invalid data: {str(e)}")

    async def read(self, resource_id: str) -> Dict[str, Any]:
        """Read a single resource by ID from the database.

        Args:
            resource_id: The ID of the resource

        Returns:
            The resource data

        Raises:
            NotFoundError: If resource doesn't exist
        """
        db_resource = self.session.get(self.model, resource_id)
        if not db_resource:
            raise NotFoundError(f"{self.resource_name} with ID {resource_id} not found")

        return self.to_dto(db_resource)

    async def update(
        self, resource_id: str, data: Dict[str, Any], partial: bool = False
    ) -> Dict[str, Any]:
        """Update an existing resource in the database.

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
        db_resource = self.session.get(self.model, resource_id)
        if not db_resource:
            raise NotFoundError(f"{self.resource_name} with ID {resource_id} not found")

        try:
            # Transform API data to database format
            update_data = self.from_api(data.copy())
            
            # Call before_update hook
            update_data = await self.before_update(resource_id, update_data)

            if partial:
                # PATCH: Update only provided fields
                # Remove None values that come from transformation
                update_data = {k: v for k, v in update_data.items() if v is not None}
                for key, value in update_data.items():
                    if hasattr(db_resource, key):
                        setattr(db_resource, key, value)
            else:
                # PUT: Replace entire resource (except system fields)
                # Preserve system fields with their original types
                update_data["id"] = resource_id
                if hasattr(db_resource, "created_at") and db_resource.created_at is not None:
                    update_data["created_at"] = db_resource.created_at

                # Create new instance to validate all fields
                for key, value in update_data.items():
                    if hasattr(db_resource, key):
                        # Handle datetime field conversion
                        if key in ["created_at", "updated_at"] and isinstance(value, str):
                            try:
                                # Try to parse ISO format datetime string
                                if value.endswith('Z'):
                                    value = value.replace('Z', '+00:00')
                                value = datetime.fromisoformat(value)
                            except (ValueError, AttributeError):
                                # If parsing fails, skip this field to preserve original
                                continue
                        setattr(db_resource, key, value)

            # Update timestamp
            if hasattr(db_resource, "updated_at"):
                db_resource.updated_at = datetime.now(timezone.utc)

            self.session.add(db_resource)
            self.session.commit()
            self.session.refresh(db_resource)
            
            # Call after_update hook
            await self.after_update(db_resource)

            return self.to_dto(db_resource)

        except Exception as e:
            self.session.rollback()
            raise ValidationError(f"Invalid data: {str(e)}")

    async def delete(self, resource_id: str) -> None:
        """Delete a resource from the database.

        Args:
            resource_id: The ID of the resource

        Raises:
            NotFoundError: If resource doesn't exist
        """
        db_resource = self.session.get(self.model, resource_id)
        if not db_resource:
            raise NotFoundError(f"{self.resource_name} with ID {resource_id} not found")
        
        # Call before_delete hook
        await self.before_delete(resource_id)

        self.session.delete(db_resource)
        self.session.commit()
        
        # Call after_delete hook
        await self.after_delete(resource_id)

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> List[Dict[str, Any]]:
        """List resources from the database with filtering.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            **filters: Additional filter parameters

        Returns:
            List of resources matching the filters
        """
        # Start with base query
        query = select(self.model)

        # Apply filters using hook
        query = self.build_list_query(query, filters)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        results = self.session.exec(query).all()

        # Convert to DTOs
        return [self.to_dto(resource) for resource in results]

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to SQLModel query.

        Args:
            query: SQLModel select query
            filters: Filter parameters

        Returns:
            Filtered query
        """
        conditions = []

        for key, value in filters.items():
            # Skip pagination parameters
            if key in ("limit", "offset"):
                continue

            # Get the field from the model
            field_name = key
            if key.endswith("__gte"):
                field_name = key[:-5]
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    conditions.append(field >= value)
            elif key.endswith("__lte"):
                field_name = key[:-5]
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    conditions.append(field <= value)
            elif key.endswith("__contains"):
                field_name = key[:-10]
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    conditions.append(field.contains(value))
            else:
                # Exact match
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    conditions.append(field == value)

        if conditions:
            query = query.where(and_(*conditions))

        return query
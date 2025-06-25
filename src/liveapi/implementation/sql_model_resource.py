"""SQLModel-based resource service for database persistence."""

from typing import Dict, Any, List, Type
from datetime import datetime, timezone
import uuid

from sqlmodel import SQLModel, Session, select, and_
from sqlalchemy.exc import IntegrityError

from .exceptions import NotFoundError, ValidationError, ConflictError


class SQLModelResource:
    """Database-backed resource service using SQLModel.

    This class provides the same interface as DefaultResource but
    persists data to a SQL database using SQLModel.
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
            # Create SQLModel instance for validation
            resource_data = data.copy()

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

            # Convert to dict for return
            return self._model_to_dict(db_resource)

        except IntegrityError as e:
            raise ConflictError(f"Database constraint violation: {str(e)}")
        except Exception as e:
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

        return self._model_to_dict(db_resource)

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
            update_data = data.copy()

            if partial:
                # PATCH: Update only provided fields
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

            return self._model_to_dict(db_resource)

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

        self.session.delete(db_resource)
        self.session.commit()

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

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        results = self.session.exec(query).all()

        # Convert to dicts
        return [self._model_to_dict(resource) for resource in results]

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

    def _model_to_dict(self, model_instance: SQLModel) -> Dict[str, Any]:
        """Convert SQLModel instance to dictionary.

        Args:
            model_instance: SQLModel instance

        Returns:
            Dictionary representation of the model
        """
        return model_instance.model_dump(mode="json")

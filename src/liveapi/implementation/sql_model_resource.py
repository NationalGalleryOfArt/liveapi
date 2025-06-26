"""SQLModel-based resource service for database persistence."""

from typing import Type
from sqlmodel import SQLModel, Session

from .base_sql_model_resource import BaseSQLModelResource


class SQLModelResource(BaseSQLModelResource):
    """Database-backed resource service using SQLModel.

    This class provides the same interface as DefaultResource but
    persists data to a SQL database using SQLModel.
    
    It inherits from BaseSQLModelResource which contains the core
    CRUD logic. Subclasses can override the hook methods to customize
    behavior without reimplementing the entire CRUD operations.
    """

    def __init__(self, model: Type[SQLModel], resource_name: str, session: Session):
        """Initialize the SQL resource service.

        Args:
            model: SQLModel class for the resource
            resource_name: Name of the resource (e.g., "users")
            session: The database session to use for operations.
        """
        super().__init__(model=model, resource_name=resource_name, session=session)
    
    # All hook methods use the default implementations from BaseSQLModelResource
    # Subclasses can override any of these methods to customize behavior
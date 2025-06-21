"""Base classes for automatic implementations."""

from typing import Dict, Any, Tuple, Optional, List
from abc import ABC, abstractmethod
from .exceptions import NotFoundError, ValidationError, ConflictError


class BaseCrudImplementation(ABC):
    """
    Base class for CRUD implementations, inspired by Rails controllers.
    
    Provides standard CRUD methods that can be overridden:
    - index() -> GET /resources (list)
    - show() -> GET /resources/:id
    - create() -> POST /resources  
    - update() -> PUT/PATCH /resources/:id
    - destroy() -> DELETE /resources/:id
    """
    
    # Override in subclass
    resource_name: str = None
    
    def __init__(self):
        """Initialize the implementation."""
        self.data_store = self.get_data_store()
    
    # Abstract methods that subclasses should implement
    @abstractmethod
    def get_data_store(self) -> Dict[str, Any]:
        """
        Return the data storage mechanism.
        
        Examples:
        - return {} (in-memory dict)
        - return self.database.get_collection(self.resource_name)
        - return RedisClient()
        """
        pass
    
    # Standard CRUD methods with sensible defaults
    def index(self, filters: Optional[Dict] = None, auth_info: Optional[Dict] = None) -> Tuple[List[Dict], int]:
        """
        List resources - GET /resources
        
        Args:
            filters: Query parameters for filtering/pagination
            auth_info: Authentication context
            
        Returns:
            Tuple of (list of resources, status_code)
        """
        # Default implementation - return all resources
        resources = list(self.data_store.values())
        
        # Apply basic filtering if provided
        if filters:
            limit = filters.get('limit', 100)
            offset = filters.get('offset', 0)
            resources = resources[offset:offset + limit]
        
        return resources, 200
    
    def show(self, resource_id: str, auth_info: Optional[Dict] = None) -> Tuple[Dict, int]:
        """
        Show single resource - GET /resources/:id
        
        Args:
            resource_id: ID of the resource to retrieve
            auth_info: Authentication context
            
        Returns:
            Tuple of (resource_data, status_code)
        """
        if resource_id not in self.data_store:
            raise NotFoundError(f"{self.resource_name.title()} {resource_id} not found")
        
        return self.data_store[resource_id], 200
    
    def create(self, data: Dict, auth_info: Optional[Dict] = None) -> Tuple[Dict, int]:
        """
        Create resource - POST /resources
        
        Args:
            data: Resource data to create
            auth_info: Authentication context
            
        Returns:
            Tuple of (created_resource, status_code)
        """
        # Validate the data
        self.validate_create(data)
        
        # Generate ID (override this method for custom ID generation)
        resource_id = self.generate_id(data)
        
        # Check for conflicts
        if resource_id in self.data_store:
            raise ConflictError(f"{self.resource_name.title()} with ID {resource_id} already exists")
        
        # Create the resource
        resource = self.build_resource(data, resource_id)
        self.data_store[resource_id] = resource
        
        return resource, 201
    
    def update(self, resource_id: str, data: Dict, auth_info: Optional[Dict] = None) -> Tuple[Dict, int]:
        """
        Update resource - PUT/PATCH /resources/:id
        
        Args:
            resource_id: ID of the resource to update
            data: Updated resource data
            auth_info: Authentication context
            
        Returns:
            Tuple of (updated_resource, status_code)
        """
        if resource_id not in self.data_store:
            raise NotFoundError(f"{self.resource_name.title()} {resource_id} not found")
        
        # Validate the data
        self.validate_update(data)
        
        # Update the resource
        existing_resource = self.data_store[resource_id]
        updated_resource = self.merge_updates(existing_resource, data)
        self.data_store[resource_id] = updated_resource
        
        return updated_resource, 200
    
    def destroy(self, resource_id: str, auth_info: Optional[Dict] = None) -> Tuple[Dict, int]:
        """
        Delete resource - DELETE /resources/:id
        
        Args:
            resource_id: ID of the resource to delete
            auth_info: Authentication context
            
        Returns:
            Tuple of (response_data, status_code)
        """
        if resource_id not in self.data_store:
            raise NotFoundError(f"{self.resource_name.title()} {resource_id} not found")
        
        # Perform any pre-deletion validation
        self.validate_destroy(resource_id)
        
        # Delete the resource
        del self.data_store[resource_id]
        
        return {"message": f"{self.resource_name.title()} deleted successfully"}, 204
    
    # Hook methods for customization
    def validate_create(self, data: Dict) -> None:
        """Override to add custom create validation."""
        # Default: check for required 'name' field
        if not data.get('name'):
            raise ValidationError("Name is required")
    
    def validate_update(self, data: Dict) -> None:
        """Override to add custom update validation."""
        # Default: no validation
        pass
    
    def validate_destroy(self, resource_id: str) -> None:
        """Override to add custom deletion validation."""
        # Default: no validation
        pass
    
    def generate_id(self, data: Dict) -> str:
        """Override to customize ID generation."""
        # Default: use name field, convert to slug
        name = data.get('name', 'unknown')
        return name.lower().replace(' ', '_').replace('-', '_')
    
    def build_resource(self, data: Dict, resource_id: str) -> Dict:
        """Override to customize resource creation."""
        return {
            "id": resource_id,
            "name": data.get('name'),
            "status": "active",
            "created_at": "2023-01-01T00:00:00Z",
            **data  # Include all provided data
        }
    
    def merge_updates(self, existing: Dict, updates: Dict) -> Dict:
        """Override to customize how updates are merged."""
        merged = existing.copy()
        merged.update(updates)
        merged["updated_at"] = "2023-01-01T00:00:00Z"
        return merged


class BaseImplementation:
    """
    Simple base class for non-CRUD implementations.
    
    Use this when you don't need standard CRUD operations
    or want full control over method implementations.
    """
    
    def __init__(self):
        """Initialize the implementation."""
        self.data_store = {}
        self.external_service_url = "https://api.example.com"
    
    async def get_data(self, resource_type: str, resource_id: str, auth_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Example data fetching method that demonstrates proper patterns.
        
        This shows how to:
        - Handle external service calls
        - Implement proper exception handling
        - Transform data between external and API formats
        - Include authentication context
        """
        try:
            # Example 1: Database/cache lookup
            cache_key = f"{resource_type}:{resource_id}"
            if cache_key in self.data_store:
                return self.data_store[cache_key]
            
            # Example 2: External service call (uncomment and adapt as needed)
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     headers = {"Authorization": f"Bearer {auth_info.get('token', '')}"} if auth_info else {}
            #     response = await client.get(f"{self.external_service_url}/{resource_type}/{resource_id}", headers=headers)
            #     
            #     if response.status_code == 404:
            #         raise NotFoundError(f"{resource_type.title()} {resource_id} not found")
            #     elif response.status_code == 401:
            #         raise UnauthorizedError("Invalid or expired authentication")
            #     elif response.status_code == 403:
            #         raise ForbiddenError("Insufficient permissions")
            #     elif response.status_code == 429:
            #         raise RateLimitError("Rate limit exceeded")
            #     elif response.status_code >= 500:
            #         raise ServiceUnavailableError("External service temporarily unavailable")
            #     
            #     response.raise_for_status()
            #     external_data = response.json()
            
            # Example 3: Data transformation
            # Transform external format to your API format
            external_data = {"id": resource_id, "type": resource_type, "status": "active"}  # Placeholder
            
            transformed_data = {
                "id": external_data["id"],
                "type": external_data["type"],
                "status": external_data["status"],
                "created_at": "2023-01-01T00:00:00Z",  # Add timestamps, computed fields, etc.
                "metadata": {
                    "source": "external_service",
                    "fetched_at": "2023-01-01T00:00:00Z"
                }
            }
            
            # Cache the result
            self.data_store[cache_key] = transformed_data
            
            return transformed_data
            
        except (ConnectionError, TimeoutError) as e:
            # Network issues
            from .exceptions import ServiceUnavailableError
            raise ServiceUnavailableError(f"Unable to fetch {resource_type} data: {str(e)}")
        except Exception as e:
            # Log the error and return a safe response
            print(f"Unexpected error fetching {resource_type} {resource_id}: {e}")
            from .exceptions import ServiceUnavailableError
            raise ServiceUnavailableError("Data service temporarily unavailable")
"""Execution logic for synchronization operations - CRUD mode."""

from pathlib import Path
from typing import Optional, Dict, Any, List
import sys

from .models import SyncAction, SyncItem, SyncPlan
from .plan import preview_sync_plan
from .crud_sync import create_crud_main_py, sync_crud_implementation


def execute_sync_plan(
    plan: SyncPlan,
    preview_only: bool,
    backup_dir: Path,
    metadata_manager,
    change_detector,
    project_root: Path,
    use_scaffold: bool = False,
) -> bool:
    """Execute a synchronization plan for both CRUD+ and scaffold modes."""
    if preview_only:
        preview_sync_plan(plan)
        return True

    if not plan.items:
        print("✅ Everything is already synchronized")
        return True

    # Choose execution mode
    if use_scaffold:
        return _execute_scaffold_mode(
            plan, project_root, metadata_manager, change_detector
        )
    else:
        return _execute_crud_mode(plan, project_root, metadata_manager, change_detector)


def _execute_crud_mode(
    plan: SyncPlan, project_root: Path, metadata_manager, change_detector
) -> bool:
    """Execute sync plan using CRUD+ mode."""
    print("🚀 LiveAPI CRUD+ Mode - No code generation needed!")
    print("   Your APIs will be served dynamically from OpenAPI specs")

    success_count = 0
    spec_files = []

    for item in plan.items:
        try:
            # For CRUD mode, we just validate the spec exists
            if sync_crud_implementation(item.source_path, project_root):
                success_count += 1
                spec_files.append(item.source_path)
            else:
                print(f"❌ Failed to sync: {item.description}")
        except Exception as e:
            print(f"❌ Error syncing {item.description}: {e}")

    # Create main.py for CRUD mode
    if success_count > 0 and spec_files:
        create_crud_main_py(spec_files, project_root)
        _update_sync_metadata(metadata_manager, change_detector)
        print(f"✅ Successfully prepared {success_count} CRUD+ APIs")
        print("🎯 Run 'liveapi run' or 'python main.py' to start your API server")
        return True
    else:
        print(f"⚠️  Prepared {success_count} of {len(plan.items)} APIs")
        return False


def _execute_scaffold_mode(
    plan: SyncPlan, project_root: Path, metadata_manager, change_detector
) -> bool:
    """Execute sync plan using scaffold generation mode."""
    print("🏗️  LiveAPI Scaffold Mode - Generating customizable service files...")

    success_count = 0
    implementations_dir = project_root / "implementations"
    implementations_dir.mkdir(exist_ok=True)

    for item in plan.items:
        try:
            # Generate implementation file directly (no templates needed)
            if _generate_implementation_file(
                item.source_path, implementations_dir, project_root
            ):
                success_count += 1
            else:
                print(f"❌ Failed to generate: {item.description}")
        except Exception as e:
            print(f"❌ Error generating {item.description}: {e}")

    # Also create main.py for easy running
    if success_count > 0:
        _create_main_py_for_implementations(project_root)
        _update_sync_metadata(metadata_manager, change_detector)
        print(f"✅ Successfully generated {success_count} implementation files")
        print("📁 Files created in implementations/ directory")
        print("🎯 Customize your services in implementations/ for real data stores")
        return True
    else:
        print(f"⚠️  Generated {success_count} of {len(plan.items)} implementations")
        return False


def _generate_implementation_file(
    spec_path: Path, implementations_dir: Path, project_root: Path
) -> bool:
    """Generate an implementation file that inherits from CRUD handlers."""
    try:
        # Parse spec to get resource name
        import yaml

        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)

        # Extract resource name from spec
        resource_name = _extract_resource_name_from_spec(spec, spec_path)
        class_name = f"{resource_name.capitalize()}Service"

        # Create implementation file content
        relative_spec = spec_path.relative_to(project_root)
        content = f'''"""
{class_name} - Database-connected implementation for {resource_name} API.

This service overrides LiveAPI's CRUD operations to connect to real data stores
while maintaining the same API interface.
"""

from liveapi.implementation import create_app
from liveapi.implementation.crud_handlers import BaseCRUDRouter
from typing import Dict, List, Any, Optional
import uuid


class {class_name}(BaseCRUDRouter):
    """
    Custom {resource_name} service with database integration.
    
    Override the CRUD methods below to:
    - Connect to your database (PostgreSQL, MongoDB, etc.)
    - Add business logic and validation
    - Implement proper error handling
    - Add logging and monitoring
    """
    
    def __init__(self):
        """Initialize your database connections."""
        # TODO: Initialize your database connection
        # self.db = YourDatabaseConnection()
        # self.logger = YourLogger()
        
        # For now, using in-memory storage (replace with your database)
        self._storage: Dict[str, Dict[str, Any]] = {{}}
    
    async def create_{resource_name}(self, {resource_name}_data: dict) -> dict:
        """
        Create a new {resource_name} in your database.
        
        Args:
            {resource_name}_data: Validated {resource_name} data from the API
            
        Returns:
            Created {resource_name} with ID
            
        Raises:
            ValidationError: When data validation fails
            ConflictError: When {resource_name} already exists
            HTTPException: For other errors (database connection, etc.)
            
        TODO: Replace with your database insert logic
        """
        from fastapi import HTTPException
        from liveapi.implementation.exceptions import ValidationError, ConflictError
        
        try:
            # Example business validation
            if not {resource_name}_data.get("site"):
                raise ValidationError(
                    message="Site is required",
                    details={{"field": "site", "error": "missing_required_field"}}
                )
            
            # Generate ID (replace with your ID generation strategy)
            {resource_name}_id = str(uuid.uuid4())
            
            # Check for duplicates (example business logic)
            existing = None  # TODO: Replace with your duplicate check
            # existing = await self.db.find_one("{resource_name}s", {{
            #     "site": {resource_name}_data["site"], 
            #     "room": {resource_name}_data["room"]
            # }})
            if existing:
                raise ConflictError(
                    message=f"{resource_name.capitalize()} already exists at this site and room",
                    details={{"site": {resource_name}_data["site"], "room": {resource_name}_data["room"]}}
                )
            
            # TODO: Replace this with your database insert
            # Example:
            # try:
            #     result = await self.db.insert_one("{resource_name}s", {{
            #         "id": {resource_name}_id,
            #         **{resource_name}_data,
            #         "created_at": datetime.utcnow(),
            #         "updated_at": datetime.utcnow()
            #     }})
            #     if not result.inserted_id:
            #         raise HTTPException(status_code=500, detail="Failed to create {resource_name}")
            # except DatabaseConnectionError as e:
            #     raise HTTPException(status_code=503, detail="Database unavailable")
            # except Exception as db_error:
            #     raise HTTPException(status_code=500, detail=f"Unexpected error: {{str(db_error)}}")
            
            # In-memory implementation (replace with database)
            {resource_name}_record = {{
                "id": {resource_name}_id, 
                **{resource_name}_data,
                "created_at": "2024-01-01T00:00:00Z",  # TODO: Use real timestamp
                "updated_at": "2024-01-01T00:00:00Z"
            }}
            self._storage[{resource_name}_id] = {resource_name}_record
            
            # TODO: Add business logic here
            # - Logging: self.logger.info(f"Created {resource_name} {{{resource_name}_id}}")
            # - Cache invalidation: await self.cache.delete("list_{resource_name}s")
            # - Event publishing: await self.events.publish("{resource_name}_created", {resource_name}_record)
            # - Notifications: await self.notify_subscribers({resource_name}_record)
            
            return {resource_name}_record
            
        except (ValidationError, ConflictError):
            # Re-raise our custom exceptions (they're handled by FastAPI error handlers)
            raise
        except Exception as e:
            # Catch any unexpected errors and convert to HTTP 500
            # TODO: Add proper logging here
            # self.logger.error(f"Unexpected error creating {resource_name}: {{str(e)}}")
            raise HTTPException(
                status_code=500, 
                detail=f"Internal server error while creating {resource_name}"
            )
    
    async def get_{resource_name}(self, {resource_name}_id: str) -> Optional[dict]:
        """
        Get a {resource_name} by ID from your database.
        
        Args:
            {resource_name}_id: The {resource_name} ID
            
        Returns:
            {resource_name} data or None if not found
            
        TODO: Replace with your database query logic
        """
        # TODO: Replace this with your database query
        # Example:
        # result = await self.db.find_one("{resource_name}s", {{"id": {resource_name}_id}})
        # return result
        
        # In-memory implementation (replace with database)
        return self._storage.get({resource_name}_id)
    
    async def list_{resource_name}s(self, skip: int = 0, limit: int = 100, **filters) -> List[dict]:
        """
        List {resource_name}s with pagination and filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filter parameters
            
        Returns:
            List of {resource_name}s
            
        TODO: Replace with your database query logic
        """
        # TODO: Replace this with your database query
        # Example:
        # results = await self.db.find("{resource_name}s", filters, skip=skip, limit=limit)
        # return results
        
        # In-memory implementation (replace with database)
        all_records = list(self._storage.values())
        
        # Apply basic filtering (replace with proper database filtering)
        if filters:
            filtered_records = []
            for record in all_records:
                match = True
                for key, value in filters.items():
                    if key in record and record[key] != value:
                        match = False
                        break
                if match:
                    filtered_records.append(record)
            all_records = filtered_records
        
        # Apply pagination
        return all_records[skip:skip + limit]
    
    async def update_{resource_name}(self, {resource_name}_id: str, {resource_name}_data: dict) -> Optional[dict]:
        """
        Update a {resource_name} in your database.
        
        Args:
            {resource_name}_id: The {resource_name} ID
            {resource_name}_data: Updated {resource_name} data
            
        Returns:
            Updated {resource_name} or None if not found
            
        TODO: Replace with your database update logic
        """
        # TODO: Replace this with your database update
        # Example:
        # result = await self.db.update_one(
        #     "{resource_name}s", 
        #     {{"id": {resource_name}_id}}, 
        #     {{"$set": {resource_name}_data}}
        # )
        # return result
        
        # In-memory implementation (replace with database)
        if {resource_name}_id not in self._storage:
            return None
        
        # Update the record
        self._storage[{resource_name}_id].update({resource_name}_data)
        
        # TODO: Add business logic here
        # - Validation
        # - Logging
        # - Cache invalidation
        # - Event publishing
        
        return self._storage[{resource_name}_id]
    
    async def delete_{resource_name}(self, {resource_name}_id: str) -> bool:
        """
        Delete a {resource_name} from your database.
        
        Args:
            {resource_name}_id: The {resource_name} ID
            
        Returns:
            True if deleted, False if not found
            
        TODO: Replace with your database delete logic
        """
        # TODO: Replace this with your database delete
        # Example:
        # result = await self.db.delete_one("{resource_name}s", {{"id": {resource_name}_id}})
        # return result.deleted_count > 0
        
        # In-memory implementation (replace with database)
        if {resource_name}_id in self._storage:
            del self._storage[{resource_name}_id]
            
            # TODO: Add business logic here
            # - Logging
            # - Cache invalidation
            # - Cleanup related data
            # - Event publishing
            
            return True
        return False


# Create the FastAPI app
def create_custom_app():
    """Create FastAPI app with database-connected {resource_name} service."""
    # Create app with custom service implementation
    app = create_app("{relative_spec}", custom_handlers={{{resource_name}: {class_name}()}})
    return app


# For direct execution
if __name__ == "__main__":
    import uvicorn
    app = create_custom_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
'''

        # Write the implementation file
        impl_file = implementations_dir / f"{resource_name}_service.py"
        impl_file.write_text(content)
        print(f"📝 Generated: {impl_file}")

        return True

    except Exception as e:
        print(f"❌ Error generating implementation: {e}")
        return False


def _extract_resource_name_from_spec(spec: Dict[str, Any], spec_path: Path) -> str:
    """Extract resource name from OpenAPI spec."""
    # Try to get from paths
    paths = spec.get("paths", {})
    for path in paths.keys():
        # Extract resource from path like /users, /locations, etc.
        parts = path.strip("/").split("/")
        if parts and parts[0] and not parts[0].startswith("{"):
            resource = parts[0].lower()
            # Remove plural 's' if present
            if resource.endswith("s") and len(resource) > 1:
                return resource[:-1]
            return resource

    # Fallback to spec filename
    stem = spec_path.stem
    if stem and stem != "api":
        return stem.lower()

    return "resource"


def _create_main_py_for_implementations(project_root: Path) -> None:
    """Create main.py that uses the custom implementations."""
    main_content = '''"""
FastAPI application using custom LiveAPI implementations.

This app loads your custom service implementations from the implementations/
directory, allowing you to use your custom database connections and business logic.
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from fastapi import FastAPI

# Add implementations directory to Python path
implementations_dir = Path(__file__).parent / "implementations"
if str(implementations_dir) not in sys.path:
    sys.path.insert(0, str(implementations_dir))

app = FastAPI(
    title="Custom LiveAPI Services",
    description="LiveAPI with custom implementations for real data stores"
)

# Auto-discover and mount custom service implementations
def discover_and_mount_services():
    """Discover service files and mount their apps."""
    if not implementations_dir.exists():
        print("⚠️  No implementations directory found")
        return
    
    service_files = list(implementations_dir.glob("*_service.py"))
    if not service_files:
        print("⚠️  No service files found in implementations/")
        return
    
    print(f"🔍 Found {len(service_files)} custom services:")
    
    for service_file in service_files:
        try:
            # Import the service module
            module_name = service_file.stem
            spec = importlib.util.spec_from_file_location(module_name, service_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the custom app
            if hasattr(module, 'create_custom_app'):
                custom_app = module.create_custom_app()
                
                # Mount under resource path
                resource_name = module_name.replace('_service', '')
                mount_path = f"/{resource_name}s"  # pluralize for REST convention
                
                app.mount(mount_path, custom_app)
                print(f"✅ Mounted {module_name} at {mount_path}")
            else:
                print(f"⚠️  {service_file.name} missing create_custom_app() function")
                
        except Exception as e:
            print(f"❌ Error loading {service_file.name}: {e}")

# Mount all discovered services
discover_and_mount_services()

@app.get("/")
async def root():
    """Root endpoint showing available services."""
    return {
        "message": "LiveAPI with Custom Implementations", 
        "services": "Check /docs for available endpoints"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''

    main_file = project_root / "main.py"
    main_file.write_text(main_content)
    print(f"📝 Generated: {main_file}")


def _update_sync_metadata(metadata_manager, change_detector) -> None:
    """Update metadata after successful synchronization."""
    # Update last sync timestamp
    metadata_manager.update_last_sync()

    # Update spec tracking for all discovered specs
    for spec_file in change_detector.find_api_specs():
        change_detector.update_spec_tracking(spec_file)

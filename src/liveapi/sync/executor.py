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

        # Create a simple stub implementation file
        content = f'''"""
Stub implementation for {resource_name} service.

This file allows you to override the default CRUD+ handlers with custom database logic.
Simply uncomment and modify the methods you want to customize.
"""

from typing import Dict, List, Any, Optional
from liveapi.implementation.crud_handlers import CRUDHandlers


class {class_name}(CRUDHandlers):
    """Custom {resource_name} service implementation.
    
    Uncomment any method below to override the default in-memory behavior
    with your own database logic.
    """
    
    # async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
    #     """Create a new {resource_name} in your database."""
    #     # Add your database logic here
    #     return await super().create(data)
    
    # async def read(self, resource_id: str) -> Dict[str, Any]:
    #     """Get a {resource_name} by ID from your database."""
    #     # Add your database logic here  
    #     return await super().read(resource_id)
    
    # async def update(self, resource_id: str, data: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
    #     """Update a {resource_name} in your database."""
    #     # Add your database logic here
    #     return await super().update(resource_id, data, partial)
    
    # async def delete(self, resource_id: str) -> None:
    #     """Delete a {resource_name} from your database."""
    #     # Add your database logic here
    #     await super().delete(resource_id)
    
    # async def list(self, limit: int = 100, offset: int = 0, **filters) -> List[Dict[str, Any]]:
    #     """List {resource_name}s with pagination and filtering."""
    #     # Add your database logic here
    #     return await super().list(limit=limit, offset=offset, **filters)
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
    """Create main.py using the same approach as CRUD+ mode."""
    # Just use the standard CRUD+ main.py generation
    from .crud_sync import create_crud_main_py
    
    # Get all specification files  
    spec_files = list((project_root / "specifications").glob("*.yaml"))
    spec_files.extend(list((project_root / "specifications").glob("*.yml")))
    
    if spec_files:
        create_crud_main_py(spec_files, project_root)


def _update_sync_metadata(metadata_manager, change_detector) -> None:
    """Update metadata after successful synchronization."""
    # Update last sync timestamp
    metadata_manager.update_last_sync()

    # Update spec tracking for all discovered specs
    for spec_file in change_detector.find_api_specs():
        change_detector.update_spec_tracking(spec_file)

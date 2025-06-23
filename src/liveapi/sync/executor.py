"""Execution logic for synchronization operations - CRUD mode."""

from pathlib import Path
from typing import Optional

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
) -> bool:
    """Execute a synchronization plan for CRUD+ APIs."""
    if preview_only:
        preview_sync_plan(plan)
        return True

    if not plan.items:
        print("✅ Everything is already synchronized")
        return True

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


def _update_sync_metadata(metadata_manager, change_detector) -> None:
    """Update metadata after successful synchronization."""
    # Update last sync timestamp
    metadata_manager.update_last_sync()

    # Update spec tracking for all discovered specs
    for spec_file in change_detector.find_api_specs():
        change_detector.update_spec_tracking(spec_file)

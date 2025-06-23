"""Implementation synchronization system for liveapi - CRUD mode."""

# This file is a facade that re-exports components from the sync package
# Simplified for CRUD-only mode

from pathlib import Path
from typing import List, Optional, Union

from .sync.models import SyncAction, SyncItem, SyncPlan
from .sync.manager import SyncManager as ModularSyncManager
from .sync.plan import (
    _find_missing_implementations,
    _find_implementation_path,
    _get_default_implementation_path,
    _get_backup_path,
    _estimate_sync_effort,
    preview_sync_plan as _preview_sync_plan,
)
from .sync.executor import execute_sync_plan
from .sync.crud_sync import create_crud_main_py, sync_crud_implementation


# Re-export the main SyncManager class
SyncManager = ModularSyncManager

# Re-export models for backward compatibility
__all__ = [
    "SyncManager",
    "SyncAction",
    "SyncItem",
    "SyncPlan",
    "create_crud_main_py",
    "sync_crud_implementation",
]

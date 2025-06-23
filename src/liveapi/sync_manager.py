"""Implementation synchronization system for liveapi - CRUD mode."""

# This file is a facade that re-exports components from the sync package
# Simplified for CRUD-only mode

from .sync.models import SyncAction, SyncItem, SyncPlan
from .sync.manager import SyncManager as ModularSyncManager
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

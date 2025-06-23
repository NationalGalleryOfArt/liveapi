"""
LiveAPI - API Lifecycle Management with Postman Integration

A comprehensive toolkit for managing OpenAPI specifications throughout their lifecycle,
with first-class support for Postman collections, Git workflows, and implementation synchronization.

Built on top of the automatic framework.
"""

from .change_detector import ChangeDetector, ChangeType
from .metadata_manager import MetadataManager
from .version_manager import VersionManager, VersionType
from .sync_manager import SyncManager
from .cli import main

__version__ = "0.1.0"
__all__ = [
    "ChangeDetector",
    "ChangeType",
    "MetadataManager",
    "VersionManager",
    "VersionType",
    "SyncManager",
    "main",
]

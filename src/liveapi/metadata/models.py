"""Data models for liveapi project metadata."""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum


class ProjectStatus(Enum):
    """Project initialization status."""

    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    SYNCED = "synced"


@dataclass
class SpecMetadata:
    """Metadata for a single OpenAPI specification."""

    file_path: str
    checksum: str
    version: str
    last_modified: str
    breaking_changes: List[str]
    implementation_path: Optional[str] = None
    postman_collection_id: Optional[str] = None
    git_commit: Optional[str] = None


@dataclass
class ProjectConfig:
    """Configuration for a liveapi project."""

    project_name: str
    created_at: str
    last_sync: Optional[str] = None
    postman_workspace_id: Optional[str] = None
    git_repository: Optional[str] = None
    api_base_url: Optional[str] = None
    auto_sync: bool = True

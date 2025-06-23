"""Metadata management for liveapi projects."""

# This file is a facade that re-exports from the metadata package
# It maintains backward compatibility with existing code

from .metadata.models import ProjectConfig, SpecMetadata, ProjectStatus
from .metadata.manager import MetadataManager

__all__ = [
    "MetadataManager",
    "ProjectConfig",
    "SpecMetadata",
    "ProjectStatus",
]

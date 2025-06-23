"""Version management system for OpenAPI specifications."""

# This file is now a facade that re-exports from the version package
# The implementation has been refactored into a modular package structure


from .version import (
    Version,
    VersionType,
    VersionedSpec,
    VersionManager,
    MigrationPlan,
)

# Re-export the main classes and functions
__all__ = [
    "Version",
    "VersionType",
    "VersionedSpec",
    "VersionManager",
    "MigrationPlan",
]

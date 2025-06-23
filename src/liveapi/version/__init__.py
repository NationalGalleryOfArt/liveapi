"""Version management package for OpenAPI specifications."""

from .models import Version, VersionType, VersionedSpec
from .manager import VersionManager
from .migration import MigrationPlan, generate_migration_plan
from .comparator import (
    extract_spec_name,
    parse_versioned_filename,
    create_compatibility_matrix,
)

__all__ = [
    "Version",
    "VersionType",
    "VersionedSpec",
    "VersionManager",
    "MigrationPlan",
    "generate_migration_plan",
    "extract_spec_name",
    "parse_versioned_filename",
    "create_compatibility_matrix",
]

"""Version comparison logic."""

import re
from pathlib import Path
from typing import Optional, Tuple, Dict

from .models import VersionedSpec


def extract_spec_name(spec_path: Path) -> str:
    """Extract the base spec name from a file path."""
    name = spec_path.stem

    # Remove version suffix if present: users_v1.0.0 -> users
    version_pattern = r"_v\d+\.\d+\.\d+$"
    name = re.sub(version_pattern, "", name)

    return name


def parse_versioned_filename(file_path: Path) -> Optional[Tuple[str, str]]:
    """Parse a versioned filename to extract name and version."""
    name = file_path.stem

    # Match pattern: {name}_v{version}
    match = re.match(r"^(.+)_v(\d+\.\d+\.\d+)$", name)
    if match:
        return match.group(1), match.group(2)

    return None


def has_breaking_changes_since_v1(version: VersionedSpec) -> bool:
    """Check if a version has breaking changes since v1.0.0."""
    return version.version.major > 1


def create_compatibility_matrix(
    versions_by_spec: Dict[str, list],
) -> Dict[str, Dict[str, Dict]]:
    """Create a compatibility matrix for all specifications."""
    matrix = {}

    for spec_name, versions in versions_by_spec.items():
        matrix[spec_name] = {}

        for version in versions:
            version_str = str(version.version)
            matrix[spec_name][version_str] = {
                "is_latest": version == versions[-1] if versions else False,
                "has_breaking_changes": has_breaking_changes_since_v1(version),
                "created_at": version.created_at,
            }

    return matrix

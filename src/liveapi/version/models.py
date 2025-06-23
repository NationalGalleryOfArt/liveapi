"""Data models for version management."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Any


class VersionType(Enum):
    """Types of version bumps."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    AUTO = "auto"  # Automatically determine based on changes


@dataclass
class Version:
    """Represents a semantic version."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, version_str: str) -> "Version":
        """Parse a version string like '1.2.3'."""
        parts = version_str.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")

        try:
            return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))
        except ValueError as e:
            raise ValueError(f"Invalid version format: {version_str}") from e

    def bump(self, version_type: VersionType) -> "Version":
        """Create a new version with the specified bump."""
        if version_type == VersionType.MAJOR:
            return Version(self.major + 1, 0, 0)
        elif version_type == VersionType.MINOR:
            return Version(self.major, self.minor + 1, 0)
        elif version_type == VersionType.PATCH:
            return Version(self.major, self.minor, self.patch + 1)
        else:
            raise ValueError(f"Cannot bump version with type: {version_type}")


@dataclass
class VersionedSpec:
    """Represents a versioned OpenAPI specification."""

    name: str  # Base name without version (e.g., "users")
    version: Version
    file_path: Path
    spec_data: Dict[str, Any]
    created_at: str

    @property
    def versioned_filename(self) -> str:
        """Get the versioned filename (e.g., users_v1.0.0.yaml)."""
        return f"{self.name}_v{self.version}{self.file_path.suffix}"

"""Version management for OpenAPI specifications."""

import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, UTC

from ..metadata_manager import MetadataManager
from ..change_detector import ChangeDetector, ChangeAnalysis
from .models import Version, VersionType, VersionedSpec
from .migration import MigrationPlan, generate_migration_plan
from .comparator import (
    extract_spec_name,
    parse_versioned_filename,
    create_compatibility_matrix,
)


class VersionManager:
    """Manages versioning for OpenAPI specifications."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.metadata_manager = MetadataManager(project_root)
        self.change_detector = ChangeDetector(project_root)
        self.specifications_dir = self.project_root / "specifications"

    def get_spec_versions(self, spec_name: str) -> List[VersionedSpec]:
        """Get all versions of a specification."""
        if not self.specifications_dir.exists():
            return []

        versions = []

        # Look for versioned files: {spec_name}_v{version}.{ext}
        for spec_file in self.specifications_dir.glob(f"{spec_name}_v*.yaml"):
            version_info = parse_versioned_filename(spec_file)
            if version_info:
                name, version_str = version_info
                try:
                    version = Version.parse(version_str)
                    spec_data = self.change_detector._load_spec(spec_file)

                    versioned_spec = VersionedSpec(
                        name=name,
                        version=version,
                        file_path=spec_file,
                        spec_data=spec_data,
                        created_at=datetime.fromtimestamp(
                            spec_file.stat().st_mtime
                        ).isoformat(),
                    )
                    versions.append(versioned_spec)
                except Exception:
                    continue  # Skip invalid files

        # Sort by version
        return sorted(
            versions, key=lambda v: (v.version.major, v.version.minor, v.version.patch)
        )

    def get_latest_version(self, spec_name: str) -> Optional[VersionedSpec]:
        """Get the latest version of a specification."""
        versions = self.get_spec_versions(spec_name)
        return versions[-1] if versions else None

    def create_version(
        self,
        spec_path: Path,
        version_type: VersionType = VersionType.AUTO,
        target_version: str = None,
    ) -> VersionedSpec:
        """Create a new version of a specification."""
        # Ensure specifications directory exists
        self.specifications_dir.mkdir(exist_ok=True)

        # Parse spec name and current version
        spec_name = extract_spec_name(spec_path)
        current_versions = self.get_spec_versions(spec_name)

        # Determine new version
        if target_version:
            new_version = Version.parse(target_version)
        else:
            if current_versions:
                latest_version = current_versions[-1].version

                if version_type == VersionType.AUTO:
                    # Analyze changes to determine version type
                    version_type = self._determine_version_type(
                        spec_path, current_versions[-1]
                    )

                new_version = latest_version.bump(version_type)
            else:
                # First version
                new_version = Version(1, 0, 0)

        # Create new versioned file
        new_filename = f"{spec_name}_v{new_version}.yaml"
        new_file_path = self.specifications_dir / new_filename

        if new_file_path.exists():
            raise ValueError(f"Version {new_version} already exists for {spec_name}")

        # Copy spec to new versioned file
        shutil.copy2(spec_path, new_file_path)

        # Update version in the spec content
        self._update_spec_version(new_file_path, str(new_version))

        # Load the new spec data
        spec_data = self.change_detector._load_spec(new_file_path)

        # Create versioned spec object
        versioned_spec = VersionedSpec(
            name=spec_name,
            version=new_version,
            file_path=new_file_path,
            spec_data=spec_data,
            created_at=datetime.now(UTC).isoformat(),
        )

        # Update tracking
        self.change_detector.update_spec_tracking(new_file_path)

        # Create latest symlink
        self._update_latest_symlink(spec_name, new_file_path)

        return versioned_spec

    def compare_versions(
        self, spec_name: str, from_version: str, to_version: str
    ) -> ChangeAnalysis:
        """Compare two versions of a specification."""
        versions = self.get_spec_versions(spec_name)
        version_map = {str(v.version): v for v in versions}

        if from_version not in version_map:
            raise ValueError(f"Version {from_version} not found for {spec_name}")
        if to_version not in version_map:
            raise ValueError(f"Version {to_version} not found for {spec_name}")

        from_spec = version_map[from_version]
        to_spec = version_map[to_version]

        # Use change detector to analyze differences
        return self.change_detector._analyze_spec_changes(
            to_spec.file_path, from_spec.spec_data, to_spec.spec_data
        )

    def generate_migration_plan(
        self, spec_name: str, from_version: str, to_version: str
    ) -> MigrationPlan:
        """Generate a migration plan between two versions."""
        analysis = self.compare_versions(spec_name, from_version, to_version)
        from_version_obj = Version.parse(from_version)
        to_version_obj = Version.parse(to_version)

        return generate_migration_plan(analysis, from_version_obj, to_version_obj)

    def get_compatibility_matrix(self) -> Dict[str, Dict[str, Dict]]:
        """Get compatibility matrix for all specifications."""
        if not self.specifications_dir.exists():
            return {}

        all_specs = set()
        for spec_file in self.specifications_dir.glob("*.yaml"):
            if spec_file.is_file():
                spec_name = extract_spec_name(spec_file)
                all_specs.add(spec_name)

        versions_by_spec = {}
        for spec_name in all_specs:
            versions = self.get_spec_versions(spec_name)
            if versions:
                versions_by_spec[spec_name] = versions

        return create_compatibility_matrix(versions_by_spec)

    def _determine_version_type(
        self, spec_path: Path, latest_version: VersionedSpec
    ) -> VersionType:
        """Automatically determine version type based on changes."""
        try:
            # Analyze changes between current spec and latest version
            current_spec = self.change_detector._load_spec(spec_path)
            analysis = self.change_detector._analyze_spec_changes(
                spec_path, latest_version.spec_data, current_spec
            )

            if analysis.is_breaking:
                return VersionType.MAJOR
            elif analysis.changes:
                return VersionType.MINOR
            else:
                return VersionType.PATCH

        except Exception:
            # Default to minor if we can't analyze
            return VersionType.MINOR

    def _update_spec_version(self, spec_path: Path, version: str) -> None:
        """Update the version field in an OpenAPI specification."""
        try:
            import yaml

            # Load spec
            with open(spec_path, "r") as f:
                spec_data = yaml.safe_load(f)

            # Update version
            if "info" not in spec_data:
                spec_data["info"] = {}
            spec_data["info"]["version"] = version

            # Save back to file
            with open(spec_path, "w") as f:
                yaml.dump(spec_data, f, default_flow_style=False, sort_keys=False)

        except Exception:
            # If we can't update the version, that's OK - the filename is the source of truth
            pass

    def _update_latest_symlink(self, spec_name: str, latest_file: Path) -> None:
        """Create or update a 'latest' symlink to the newest version."""
        latest_dir = self.specifications_dir / "latest"
        latest_dir.mkdir(exist_ok=True)

        symlink_path = latest_dir / f"{spec_name}.yaml"

        # Remove existing symlink
        if symlink_path.exists() or symlink_path.is_symlink():
            symlink_path.unlink()

        # Create new symlink (relative path)
        relative_path = Path("..") / latest_file.name
        symlink_path.symlink_to(relative_path)

    def _extract_spec_name(self, spec_path: Path) -> str:
        """Extract the base spec name from a file path."""
        # Delegate to the standalone function for implementation
        return extract_spec_name(spec_path)

    def _parse_versioned_filename(self, file_path: Path) -> Optional[Tuple[str, str]]:
        """Parse a versioned filename to extract name and version."""
        # Delegate to the standalone function for implementation
        return parse_versioned_filename(file_path)

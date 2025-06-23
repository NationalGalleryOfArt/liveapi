"""Main change detector implementation."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..metadata_manager import MetadataManager, SpecMetadata
from .models import ChangeAnalysis
from .utils import load_spec, is_openapi_spec
from .analyzer import analyze_new_spec, analyze_spec_changes


class ChangeDetector:
    """Detects and analyzes changes in OpenAPI specifications."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.metadata_manager = MetadataManager(project_root)

        # Paths that indicate breaking changes when modified
        self.breaking_change_paths = {
            "paths.*.*.parameters",
            "paths.*.*.responses",
            "paths.*.*.requestBody.required",
            "components.schemas.*.required",
            "components.schemas.*.properties.*.type",
            "info.version",  # Major version changes
        }

    def find_api_specs(self) -> List[Path]:
        """Find all OpenAPI specification files in the project."""
        specs = []

        # Look in specifications directory first
        specs_dir = self.project_root / "specifications"
        if specs_dir.exists():
            for pattern in ["*.yaml", "*.yml", "*.json"]:
                specs.extend(specs_dir.glob(pattern))

        # Also check current directory if no specifications directory
        if not specs:
            for pattern in ["*.yaml", "*.yml", "*.json"]:
                for file_path in self.project_root.glob(pattern):
                    if is_openapi_spec(file_path):
                        specs.append(file_path)

        return sorted(specs)

    def detect_all_changes(self) -> Dict[str, ChangeAnalysis]:
        """Detect changes in all OpenAPI specifications."""
        changes = {}

        for spec_path in self.find_api_specs():
            analysis = self.detect_changes(spec_path)
            if analysis and analysis.changes:
                changes[str(spec_path)] = analysis

        return changes

    def detect_changes(self, spec_path: Path) -> Optional[ChangeAnalysis]:
        """Detect changes in a single OpenAPI specification."""
        if not spec_path.exists():
            return None

        specs_metadata = self.metadata_manager.load_specs_metadata()
        spec_key = str(spec_path)

        # Check if this is a new file
        if spec_key not in specs_metadata:
            return analyze_new_spec(spec_path)

        # Check if file has changed
        current_checksum = self.metadata_manager.get_spec_checksum(spec_path)
        stored_metadata = specs_metadata[spec_key]

        if current_checksum == stored_metadata.checksum:
            return None  # No changes

        # Load old and new specifications
        try:
            old_spec = self._load_cached_spec(stored_metadata)
            new_spec = load_spec(spec_path)

            return analyze_spec_changes(spec_path, old_spec, new_spec)
        except Exception as e:
            # If we can't load the old spec, treat as modified
            from .models import Change, ChangeType

            return ChangeAnalysis(
                spec_path=str(spec_path),
                changes=[
                    Change(
                        change_type=ChangeType.MODIFIED,
                        path="",
                        description=f"Unable to analyze changes: {e}",
                        is_breaking=True,
                    )
                ],
                is_breaking=True,
                summary="Specification modified (unable to analyze specific changes)",
            )

    def update_spec_tracking(self, spec_path: Path) -> None:
        """Update tracking information for a specification."""
        current_checksum = self.metadata_manager.get_spec_checksum(spec_path)

        # Load current spec to extract version info
        try:
            spec_data = load_spec(spec_path)
            version = spec_data.get("info", {}).get("version", "1.0.0")
        except Exception:
            version = "1.0.0"

        metadata = SpecMetadata(
            file_path=str(spec_path),
            checksum=current_checksum,
            version=version,
            last_modified=spec_path.stat().st_mtime_ns,
            breaking_changes=[],
        )

        self.metadata_manager.update_spec_metadata(spec_path, metadata)

        # Cache the current spec content for future comparisons
        self._cache_spec_content(spec_path, spec_data)

    def _cache_spec_content(self, spec_path: Path, spec_data: Dict) -> None:
        """Cache specification content for future comparisons."""
        cache_dir = self.metadata_manager.metadata_dir / "cache"
        cache_dir.mkdir(exist_ok=True)

        cache_file = cache_dir / f"{spec_path.stem}.json"
        with open(cache_file, "w") as f:
            json.dump(spec_data, f, indent=2)

    def _load_cached_spec(self, metadata: SpecMetadata) -> Dict:
        """Load cached specification content."""
        cache_dir = self.metadata_manager.metadata_dir / "cache"
        spec_path = Path(metadata.file_path)
        cache_file = cache_dir / f"{spec_path.stem}.json"

        if cache_file.exists():
            with open(cache_file, "r") as f:
                return json.load(f)

        # Fallback: try to load from original path if cache doesn't exist
        return load_spec(spec_path)

    def _load_spec(self, spec_path: Path) -> Dict[str, Any]:
        """Load an OpenAPI specification from file.

        This method is kept for backward compatibility.
        """
        return load_spec(spec_path)

    def _analyze_spec_changes(
        self, spec_path: Path, old_spec: Dict, new_spec: Dict
    ) -> ChangeAnalysis:
        """Analyze changes between two OpenAPI specifications.

        This method is kept for backward compatibility.
        """
        return analyze_spec_changes(spec_path, old_spec, new_spec)

    def _is_openapi_spec(self, file_path: Path) -> bool:
        """Check if a file is an OpenAPI specification.

        This method is kept for backward compatibility.
        """
        return is_openapi_spec(file_path)

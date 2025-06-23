"""Manager for liveapi project metadata."""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, UTC
from dataclasses import asdict

from .models import ProjectConfig, SpecMetadata, ProjectStatus
from .utils import calculate_checksum, update_gitignore


class MetadataManager:
    """Manages liveapi project metadata and configuration."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.metadata_dir = self.project_root / ".liveapi"
        self.config_file = self.metadata_dir / "config.json"
        self.specs_file = self.metadata_dir / "specs.json"
        self.checksums_file = self.metadata_dir / "checksums.json"

    def initialize_project(
        self, project_name: str = None, api_base_url: str = None
    ) -> ProjectConfig:
        """Initialize a new liveapi project."""
        if project_name is None:
            project_name = self.project_root.name

        # Create metadata directory
        self.metadata_dir.mkdir(exist_ok=True)

        # Create project configuration
        config = ProjectConfig(
            project_name=project_name,
            created_at=datetime.now(UTC).isoformat(),
            api_base_url=api_base_url,
        )

        self.save_config(config)

        # Initialize empty specs tracking
        self.save_specs_metadata({})

        # Create .gitignore entry for generated files
        update_gitignore(self.project_root)

        return config

    def get_project_status(self) -> ProjectStatus:
        """Get the current project status."""
        if not self.metadata_dir.exists():
            return ProjectStatus.UNINITIALIZED

        if not self.config_file.exists():
            return ProjectStatus.UNINITIALIZED

        config = self.load_config()
        if config and config.last_sync:
            return ProjectStatus.SYNCED

        return ProjectStatus.INITIALIZED

    def load_config(self) -> Optional[ProjectConfig]:
        """Load project configuration."""
        if not self.config_file.exists():
            return None

        with open(self.config_file, "r") as f:
            data = json.load(f)
            return ProjectConfig(**data)

    def save_config(self, config: ProjectConfig) -> None:
        """Save project configuration."""
        self.metadata_dir.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(asdict(config), f, indent=2)

    def load_specs_metadata(self) -> Dict[str, SpecMetadata]:
        """Load specifications metadata."""
        if not self.specs_file.exists():
            return {}

        with open(self.specs_file, "r") as f:
            data = json.load(f)
            return {path: SpecMetadata(**spec_data) for path, spec_data in data.items()}

    def save_specs_metadata(self, specs: Dict[str, SpecMetadata]) -> None:
        """Save specifications metadata."""
        self.metadata_dir.mkdir(exist_ok=True)
        data = {path: asdict(spec_metadata) for path, spec_metadata in specs.items()}
        with open(self.specs_file, "w") as f:
            json.dump(data, f, indent=2)

    def update_spec_metadata(self, spec_path: Path, metadata: SpecMetadata) -> None:
        """Update metadata for a single specification."""
        specs = self.load_specs_metadata()
        specs[str(spec_path)] = metadata
        self.save_specs_metadata(specs)

    def get_spec_checksum(self, spec_path: Path) -> str:
        """Calculate checksum for a specification file."""
        return calculate_checksum(spec_path)

    def has_spec_changed(self, spec_path: Path) -> bool:
        """Check if a specification has changed since last tracking."""
        current_checksum = self.get_spec_checksum(spec_path)
        specs = self.load_specs_metadata()

        spec_key = str(spec_path)
        if spec_key not in specs:
            return True  # New file

        return specs[spec_key].checksum != current_checksum

    def update_last_sync(self) -> None:
        """Update the last sync timestamp."""
        config = self.load_config()
        if config:
            config.last_sync = datetime.now(UTC).isoformat()
            self.save_config(config)

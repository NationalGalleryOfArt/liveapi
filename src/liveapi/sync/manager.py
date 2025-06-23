"""Main SyncManager class for synchronization operations."""

from pathlib import Path

from ..metadata_manager import MetadataManager
from ..change_detector import ChangeDetector
from ..version_manager import VersionManager
from .models import SyncPlan
from .plan import analyze_sync_requirements
from .executor import execute_sync_plan


class SyncManager:
    """Manages synchronization between specifications and implementations."""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.metadata_manager = MetadataManager(project_root)
        self.change_detector = ChangeDetector(project_root)
        self.version_manager = VersionManager(project_root)

        self.specifications_dir = self.project_root / "specifications"
        self.implementations_dir = self.project_root / "implementations"
        self.backup_dir = self.project_root / ".liveapi" / "backups"

    def analyze_sync_requirements(self) -> SyncPlan:
        """Analyze what needs to be synchronized."""
        return analyze_sync_requirements(
            self.project_root,
            self.specifications_dir,
            self.implementations_dir,
            self.change_detector,
            self.version_manager,
        )

    def execute_sync_plan(
        self, plan: SyncPlan, preview_only: bool = False, use_scaffold: bool = False
    ) -> bool:
        """Execute a synchronization plan."""
        return execute_sync_plan(
            plan,
            preview_only,
            self.backup_dir,
            self.metadata_manager,
            self.change_detector,
            self.project_root,
            use_scaffold,
        )

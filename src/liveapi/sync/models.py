"""Data models for the synchronization system."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


class SyncAction(Enum):
    """Types of sync actions."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MIGRATE = "migrate"
    NO_CHANGE = "no_change"


@dataclass
class SyncItem:
    """Represents a single synchronization item."""

    spec_name: str
    action: SyncAction
    source_path: Path
    target_path: Path
    description: str
    requires_manual_review: bool = False
    backup_path: Optional[Path] = None


@dataclass
class SyncPlan:
    """Plan for synchronizing implementations with specifications."""

    items: List[SyncItem]
    breaking_changes: List[str]
    requires_manual_review: bool
    estimated_time: str  # "low", "medium", "high"

    @property
    def create_items(self) -> List[SyncItem]:
        return [item for item in self.items if item.action == SyncAction.CREATE]

    @property
    def update_items(self) -> List[SyncItem]:
        return [item for item in self.items if item.action == SyncAction.UPDATE]

    @property
    def delete_items(self) -> List[SyncItem]:
        return [item for item in self.items if item.action == SyncAction.DELETE]

    @property
    def migrate_items(self) -> List[SyncItem]:
        return [item for item in self.items if item.action == SyncAction.MIGRATE]

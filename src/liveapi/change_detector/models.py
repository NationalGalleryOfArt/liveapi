"""Data models for change detection system."""

from enum import Enum
from dataclasses import dataclass
from typing import List, Any


class ChangeType(Enum):
    """Types of changes in OpenAPI specifications."""

    NEW = "new"
    MODIFIED = "modified"
    DELETED = "deleted"
    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"


@dataclass
class Change:
    """Represents a single change in an OpenAPI specification."""

    change_type: ChangeType
    path: str
    description: str
    old_value: Any = None
    new_value: Any = None
    is_breaking: bool = False


@dataclass
class ChangeAnalysis:
    """Analysis of changes in an OpenAPI specification."""

    spec_path: str
    changes: List[Change]
    is_breaking: bool
    summary: str

    @property
    def breaking_changes(self) -> List[Change]:
        return [c for c in self.changes if c.is_breaking]

    @property
    def non_breaking_changes(self) -> List[Change]:
        return [c for c in self.changes if not c.is_breaking]

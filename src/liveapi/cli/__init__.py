"""CLI package for liveapi."""

from .main import main
from .commands.project import handle_no_command, cmd_init, cmd_status, cmd_validate
from .commands.version import (
    cmd_version,
    cmd_version_create,
    cmd_version_list,
    cmd_version_compare,
)
from .commands.sync import cmd_sync
from .commands.generate import cmd_generate
from .commands.server import cmd_run, cmd_kill, cmd_ping
from .utils import resolve_spec_path, extract_spec_name_from_input

# Re-export classes and functions needed by tests
from ..metadata_manager import MetadataManager
from ..change_detector import ChangeDetector
from ..version_manager import VersionManager, VersionType
from ..sync_manager import SyncManager
from ..spec_generator import SpecGenerator

__all__ = [
    "main",
    "handle_no_command",
    "cmd_init",
    "cmd_status",
    "cmd_validate",
    "cmd_version",
    "cmd_version_create",
    "cmd_version_list",
    "cmd_version_compare",
    "cmd_sync",
    "cmd_generate",
    "cmd_run",
    "cmd_kill",
    "cmd_ping",
    "resolve_spec_path",
    "extract_spec_name_from_input",
    # Classes and functions needed by tests
    "MetadataManager",
    "ChangeDetector",
    "VersionManager",
    "VersionType",
    "SyncManager",
    "SpecGenerator",
]

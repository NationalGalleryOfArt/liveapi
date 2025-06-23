"""Command line interface for liveapi.

This module is kept for backward compatibility.
The actual implementation has been moved to the cli package.
"""

from .cli.main import main

# Re-export command functions for backward compatibility
from .cli.commands.project import (  # noqa: F401
    handle_no_command,
    cmd_init,
    cmd_status,
    cmd_validate,
)
from .cli.commands.version import (  # noqa: F401
    cmd_version,
    cmd_version_create,
    cmd_version_list,
    cmd_version_compare,
)
from .cli.commands.sync import cmd_sync  # noqa: F401
from .cli.commands.generate import cmd_generate, cmd_regenerate  # noqa: F401
from .cli.commands.server import cmd_run, cmd_kill, cmd_ping  # noqa: F401
from .cli.utils import resolve_spec_path, extract_spec_name_from_input  # noqa: F401

if __name__ == "__main__":
    main()

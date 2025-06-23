"""Utility functions for metadata management."""

import hashlib
from pathlib import Path


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum for a file."""
    if not file_path.exists():
        return ""

    with open(file_path, "rb") as f:
        content = f.read()
        return hashlib.sha256(content).hexdigest()


def update_gitignore(project_root: Path) -> None:
    """Add liveapi entries to .gitignore if needed."""
    gitignore_path = project_root / ".gitignore"

    liveapi_entries = [
        "# LiveAPI generated files and temporary data",
        ".liveapi/generated/",
        ".liveapi/cache/",
        ".liveapi/backups/",
        ".liveapi/uvicorn.pid",
        ".liveapi/*.log",
        "",
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if "# LiveAPI generated files" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n" + "\n".join(liveapi_entries))
    else:
        gitignore_path.write_text("\n".join(liveapi_entries))

"""Utility functions for change detection."""

import yaml
import json
from pathlib import Path
from typing import Dict, Any


def load_spec(spec_path: Path) -> Dict[str, Any]:
    """Load an OpenAPI specification from file."""
    content = spec_path.read_text()

    if spec_path.suffix.lower() in [".yaml", ".yml"]:
        return yaml.safe_load(content)
    else:
        return json.loads(content)


def is_openapi_spec(file_path: Path) -> bool:
    """Check if a file is an OpenAPI specification."""
    try:
        content = file_path.read_text()
        openapi_indicators = ["openapi:", "swagger:", '"openapi":', '"swagger":']
        return any(indicator in content.lower() for indicator in openapi_indicators)
    except Exception:
        return False


def is_major_version_bump(old_version: str, new_version: str) -> bool:
    """Check if version change represents a major version bump (breaking)."""
    try:
        old_parts = old_version.split(".")
        new_parts = new_version.split(".")

        if len(old_parts) >= 1 and len(new_parts) >= 1:
            return int(new_parts[0]) > int(old_parts[0])
    except (ValueError, IndexError):
        pass

    return False  # If we can't parse versions, assume non-breaking


def generate_change_summary(changes: list) -> str:
    """Generate a human-readable summary of changes."""
    if not changes:
        return "No changes detected"

    breaking_count = len([c for c in changes if c.is_breaking])
    total_count = len(changes)

    if breaking_count > 0:
        return f"{breaking_count} breaking changes, {total_count - breaking_count} non-breaking changes"
    else:
        return f"{total_count} non-breaking changes"

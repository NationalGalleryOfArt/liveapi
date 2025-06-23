"""Utility functions for liveapi CLI."""

from pathlib import Path
from typing import Optional


def resolve_spec_path(spec_input: str) -> Optional[Path]:
    """Resolve specification path from user input."""
    # Try as direct path first
    spec_path = Path(spec_input)
    if spec_path.exists():
        return spec_path

    # Try in current directory
    for ext in [".yaml", ".yml", ".json"]:
        candidate = Path(f"{spec_input}{ext}")
        if candidate.exists():
            return candidate

    # Try in specifications directory
    specs_dir = Path("specifications")
    if specs_dir.exists():
        for ext in [".yaml", ".yml", ".json"]:
            candidate = specs_dir / f"{spec_input}{ext}"
            if candidate.exists():
                return candidate

    return None


def extract_spec_name_from_input(spec_input: str) -> str:
    """Extract spec name from user input."""
    # Remove path and extension
    return Path(spec_input).stem.split("_v")[0]  # Remove version suffix if present

"""Analysis logic for OpenAPI specification changes."""

from pathlib import Path
from typing import Dict, List, Any

from .models import Change, ChangeAnalysis, ChangeType
from .utils import is_major_version_bump, generate_change_summary


def analyze_new_spec(spec_path: Path) -> ChangeAnalysis:
    """Analyze a new OpenAPI specification."""
    return ChangeAnalysis(
        spec_path=str(spec_path),
        changes=[
            Change(
                change_type=ChangeType.NEW,
                path="",
                description=f"New OpenAPI specification: {spec_path.name}",
                is_breaking=False,
            )
        ],
        is_breaking=False,
        summary=f"New specification added: {spec_path.name}",
    )


def analyze_spec_changes(
    spec_path: Path, old_spec: Dict, new_spec: Dict
) -> ChangeAnalysis:
    """Analyze changes between two OpenAPI specifications."""
    changes = []

    # Check version changes
    old_version = old_spec.get("info", {}).get("version", "1.0.0")
    new_version = new_spec.get("info", {}).get("version", "1.0.0")

    if old_version != new_version:
        is_breaking = is_major_version_bump(old_version, new_version)
        changes.append(
            Change(
                change_type=ChangeType.MODIFIED,
                path="info.version",
                description=f"Version changed from {old_version} to {new_version}",
                old_value=old_version,
                new_value=new_version,
                is_breaking=is_breaking,
            )
        )

    # Check path changes
    old_paths = set(old_spec.get("paths", {}).keys())
    new_paths = set(new_spec.get("paths", {}).keys())

    # Removed paths (breaking)
    for removed_path in old_paths - new_paths:
        changes.append(
            Change(
                change_type=ChangeType.DELETED,
                path=f"paths.{removed_path}",
                description=f"Removed endpoint: {removed_path}",
                old_value=removed_path,
                is_breaking=True,
            )
        )

    # Added paths (non-breaking)
    for added_path in new_paths - old_paths:
        changes.append(
            Change(
                change_type=ChangeType.NEW,
                path=f"paths.{added_path}",
                description=f"Added endpoint: {added_path}",
                new_value=added_path,
                is_breaking=False,
            )
        )

    # Modified paths
    for path in old_paths & new_paths:
        path_changes = analyze_path_changes(
            path, old_spec["paths"][path], new_spec["paths"][path]
        )
        changes.extend(path_changes)

    # Analyze schema changes
    schema_changes = analyze_schema_changes(old_spec, new_spec)
    changes.extend(schema_changes)

    is_breaking = any(c.is_breaking for c in changes)

    return ChangeAnalysis(
        spec_path=str(spec_path),
        changes=changes,
        is_breaking=is_breaking,
        summary=generate_change_summary(changes),
    )


def analyze_path_changes(path: str, old_path: Dict, new_path: Dict) -> List[Change]:
    """Analyze changes in a single path definition."""
    changes = []

    old_methods = set(old_path.keys())
    new_methods = set(new_path.keys())

    # Removed methods (breaking)
    for removed_method in old_methods - new_methods:
        changes.append(
            Change(
                change_type=ChangeType.DELETED,
                path=f"paths.{path}.{removed_method}",
                description=f"Removed method {removed_method.upper()} from {path}",
                is_breaking=True,
            )
        )

    # Added methods (non-breaking)
    for added_method in new_methods - old_methods:
        changes.append(
            Change(
                change_type=ChangeType.NEW,
                path=f"paths.{path}.{added_method}",
                description=f"Added method {added_method.upper()} to {path}",
                is_breaking=False,
            )
        )

    # Modified methods
    for method in old_methods & new_methods:
        method_changes = analyze_method_changes(
            path, method, old_path[method], new_path[method]
        )
        changes.extend(method_changes)

    return changes


def analyze_method_changes(
    path: str, method: str, old_method: Dict, new_method: Dict
) -> List[Change]:
    """Analyze changes in a single method definition."""
    changes = []
    base_path = f"paths.{path}.{method}"

    # Check parameter changes
    old_params = {p.get("name"): p for p in old_method.get("parameters", [])}
    new_params = {p.get("name"): p for p in new_method.get("parameters", [])}

    # Removed parameters (breaking if required)
    for param_name in set(old_params.keys()) - set(new_params.keys()):
        old_param = old_params[param_name]
        is_breaking = old_param.get("required", False)
        changes.append(
            Change(
                change_type=ChangeType.DELETED,
                path=f"{base_path}.parameters.{param_name}",
                description=f"Removed parameter '{param_name}' from {method.upper()} {path}",
                is_breaking=is_breaking,
            )
        )

    # Added required parameters (breaking)
    for param_name in set(new_params.keys()) - set(old_params.keys()):
        new_param = new_params[param_name]
        is_breaking = new_param.get("required", False)
        changes.append(
            Change(
                change_type=ChangeType.NEW,
                path=f"{base_path}.parameters.{param_name}",
                description=f"Added parameter '{param_name}' to {method.upper()} {path}",
                is_breaking=is_breaking,
            )
        )

    return changes


def analyze_schema_changes(old_spec: Dict, new_spec: Dict) -> List[Change]:
    """Analyze changes in schema definitions."""
    changes = []

    old_schemas = old_spec.get("components", {}).get("schemas", {})
    new_schemas = new_spec.get("components", {}).get("schemas", {})

    # Removed schemas (breaking)
    for schema_name in set(old_schemas.keys()) - set(new_schemas.keys()):
        changes.append(
            Change(
                change_type=ChangeType.DELETED,
                path=f"components.schemas.{schema_name}",
                description=f"Removed schema definition: {schema_name}",
                is_breaking=True,
            )
        )

    # Added schemas (non-breaking)
    for schema_name in set(new_schemas.keys()) - set(old_schemas.keys()):
        changes.append(
            Change(
                change_type=ChangeType.NEW,
                path=f"components.schemas.{schema_name}",
                description=f"Added schema definition: {schema_name}",
                is_breaking=False,
            )
        )

    return changes

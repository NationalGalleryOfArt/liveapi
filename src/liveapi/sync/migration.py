"""Migration guide generation for breaking changes."""

from pathlib import Path

from .models import SyncItem


def create_migration_guide(item: SyncItem, guide_path: Path) -> None:
    """Create a migration guide for breaking changes."""
    # Analyze the specific changes
    try:
        # Import here to avoid circular imports
        from ..version_manager import VersionManager

        version_manager = VersionManager(Path(item.source_path).parent.parent)

        versions = version_manager.get_spec_versions(item.spec_name)
        if len(versions) >= 2:
            from_version = str(versions[-2].version)
            to_version = str(versions[-1].version)

            migration_plan = version_manager.generate_migration_plan(
                item.spec_name, from_version, to_version
            )

            guide_content = f"""# Migration Guide: {item.spec_name}

## Version Change
From: v{from_version}  
To: v{to_version}

## Breaking Changes
{chr(10).join(f"- {change}" for change in migration_plan.breaking_changes)}

## Migration Steps
{chr(10).join(f"{i}. {step}" for i, step in enumerate(migration_plan.migration_steps, 1))}

## Effort Estimate
- Complexity: {migration_plan.estimated_effort}
- Manual intervention required: {'Yes' if migration_plan.requires_manual_intervention else 'No'}

## Files
- Original implementation: {item.target_path}
- Backup: {item.backup_path}
- New template: {item.target_path.with_suffix('.v2.py')}

## Next Steps
1. Review the breaking changes above
2. Update your implementation using the new template as a guide
3. Test thoroughly before deploying
4. Update any client code that depends on the changed API
"""

            with open(guide_path, "w") as f:
                f.write(guide_content)

    except Exception:
        # Fallback generic guide
        guide_content = f"""# Migration Guide: {item.spec_name}

Breaking changes detected in your API specification.

## Files
- Original implementation: {item.target_path}
- Backup: {item.backup_path}
- New template: {item.target_path.with_suffix('.v2.py')}

## Next Steps
1. Compare the backup with the new template
2. Manually merge your custom logic
3. Test the updated implementation
4. Update any dependent code
"""
        with open(guide_path, "w") as f:
            f.write(guide_content)


def generate_migration_steps(from_spec_path: Path, to_spec_path: Path) -> list:
    """Generate migration steps based on the differences between two specs."""
    # This is a placeholder for future implementation
    # In a real implementation, this would analyze the OpenAPI specs
    # and generate specific migration steps
    return [
        "Update your endpoint handlers to match the new API structure",
        "Modify data models to accommodate schema changes",
        "Update validation logic for new constraints",
        "Test all endpoints with the new request/response formats",
    ]

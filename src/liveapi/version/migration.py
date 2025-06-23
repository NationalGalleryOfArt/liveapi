"""Migration planning between versions."""

from dataclasses import dataclass
from typing import List

from .models import Version
from ..change_detector import ChangeAnalysis


@dataclass
class MigrationPlan:
    """Plan for migrating implementations between versions."""

    from_version: Version
    to_version: Version
    breaking_changes: List[str]
    migration_steps: List[str]
    requires_manual_intervention: bool
    estimated_effort: str  # "low", "medium", "high"


def generate_migration_plan(
    analysis: ChangeAnalysis, from_version: Version, to_version: Version
) -> MigrationPlan:
    """Generate a migration plan based on change analysis."""
    breaking_changes = [c.description for c in analysis.breaking_changes]
    migration_steps = []
    requires_manual = False
    effort = "low"

    # Analyze breaking changes to generate migration steps
    for change in analysis.breaking_changes:
        if "removed" in change.description.lower():
            migration_steps.append(f"Remove deprecated code for: {change.description}")
            requires_manual = True
            effort = "high"
        elif "required" in change.description.lower():
            migration_steps.append(
                f"Update to handle new requirement: {change.description}"
            )
            requires_manual = True
            if effort == "low":
                effort = "medium"
        elif "version changed" in change.description.lower():
            migration_steps.append("Update API version references in client code")

    # Add non-breaking change steps
    for change in analysis.non_breaking_changes:
        if "added" in change.description.lower():
            migration_steps.append(
                f"Optional: Utilize new feature: {change.description}"
            )

    if not migration_steps:
        migration_steps.append("No implementation changes required")

    return MigrationPlan(
        from_version=from_version,
        to_version=to_version,
        breaking_changes=breaking_changes,
        migration_steps=migration_steps,
        requires_manual_intervention=requires_manual,
        estimated_effort=effort,
    )

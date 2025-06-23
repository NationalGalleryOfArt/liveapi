"""Planning logic for synchronization operations."""

from pathlib import Path
from typing import List

from ..change_detector import ChangeAnalysis
from .models import SyncAction, SyncItem, SyncPlan


def analyze_sync_requirements(
    project_root: Path,
    specifications_dir: Path,
    implementations_dir: Path,
    change_detector,
    version_manager,
) -> SyncPlan:
    """Analyze what needs to be synchronized."""
    items = []
    breaking_changes = []
    requires_manual_review = False

    # Get all changes since last sync
    all_changes = change_detector.detect_all_changes()

    for spec_path, analysis in all_changes.items():
        spec_name = version_manager._extract_spec_name(Path(spec_path))

        # Determine what kind of sync is needed
        sync_items = _analyze_spec_changes(
            spec_name,
            spec_path,
            analysis,
            implementations_dir,
            version_manager,
        )
        items.extend(sync_items)

        if analysis.is_breaking:
            breaking_changes.extend([c.description for c in analysis.breaking_changes])
            requires_manual_review = True

    # Also check for missing implementations (but skip specs we already processed)
    processed_specs = {Path(spec_path).name for spec_path in all_changes.keys()}
    missing_items = _find_missing_implementations(
        specifications_dir, implementations_dir, version_manager, processed_specs
    )
    items.extend(missing_items)

    # Estimate effort
    estimated_time = _estimate_sync_effort(items, breaking_changes)

    return SyncPlan(
        items=items,
        breaking_changes=breaking_changes,
        requires_manual_review=requires_manual_review,
        estimated_time=estimated_time,
    )


def _analyze_spec_changes(
    spec_name: str,
    spec_path: str,
    analysis: ChangeAnalysis,
    implementations_dir: Path,
    version_manager,
) -> List[SyncItem]:
    """Analyze changes in a specification and determine sync actions."""
    items = []

    # Find corresponding implementation
    impl_path = _find_implementation_path(spec_name, implementations_dir)

    if not impl_path:
        # No implementation exists - need to create one
        items.append(
            SyncItem(
                spec_name=spec_name,
                action=SyncAction.CREATE,
                source_path=Path(spec_path),
                target_path=_get_default_implementation_path(
                    spec_name, implementations_dir
                ),
                description=f"Create implementation for {spec_name}",
                requires_manual_review=False,
            )
        )
    else:
        # Implementation exists - determine update type
        if analysis.is_breaking:
            # Breaking changes require migration
            items.append(
                SyncItem(
                    spec_name=spec_name,
                    action=SyncAction.MIGRATE,
                    source_path=Path(spec_path),
                    target_path=impl_path,
                    description=f"Migrate {spec_name} implementation (breaking changes)",
                    requires_manual_review=True,
                    backup_path=_get_backup_path(
                        impl_path,
                        Path(spec_path).parent.parent / ".liveapi" / "backups",
                    ),
                )
            )
        else:
            # Non-breaking changes can be updated automatically
            items.append(
                SyncItem(
                    spec_name=spec_name,
                    action=SyncAction.UPDATE,
                    source_path=Path(spec_path),
                    target_path=impl_path,
                    description=f"Update {spec_name} implementation (non-breaking changes)",
                    requires_manual_review=False,
                    backup_path=_get_backup_path(
                        impl_path,
                        Path(spec_path).parent.parent / ".liveapi" / "backups",
                    ),
                )
            )

    return items


def _find_missing_implementations(
    specifications_dir: Path,
    implementations_dir: Path,
    version_manager,
    processed_specs: set = None,
) -> List[SyncItem]:
    """Find specifications that don't have implementations."""
    items = []
    processed_specs = processed_specs or set()

    if not specifications_dir.exists():
        return items

    for spec_file in specifications_dir.glob("*.yaml"):
        if spec_file.is_file() and spec_file.name not in processed_specs:
            spec_name = version_manager._extract_spec_name(spec_file)
            impl_path = _find_implementation_path(spec_name, implementations_dir)

            if not impl_path:
                items.append(
                    SyncItem(
                        spec_name=spec_name,
                        action=SyncAction.CREATE,
                        source_path=spec_file,
                        target_path=_get_default_implementation_path(
                            spec_name, implementations_dir
                        ),
                        description=f"Create missing implementation for {spec_name}",
                        requires_manual_review=False,
                    )
                )

    return items


def _find_implementation_path(spec_name: str, implementations_dir: Path):
    """Find the implementation file for a specification."""
    if not implementations_dir.exists():
        return None

    # Look for various naming patterns
    candidates = [
        f"{spec_name}_service.py",
        f"{spec_name}_implementation.py",
        f"{spec_name}.py",
        f"{spec_name}_impl.py",
    ]

    for candidate in candidates:
        impl_path = implementations_dir / candidate
        if impl_path.exists():
            return impl_path

    return None


def _get_default_implementation_path(spec_name: str, implementations_dir: Path) -> Path:
    """Get the default implementation path for a specification."""
    implementations_dir.mkdir(exist_ok=True)
    return implementations_dir / f"{spec_name}_service.py"


def _get_backup_path(impl_path: Path, backup_dir: Path) -> Path:
    """Get backup path for an implementation."""
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return backup_dir / f"{impl_path.stem}_{timestamp}{impl_path.suffix}"


def _estimate_sync_effort(items: List[SyncItem], breaking_changes: List[str]) -> str:
    """Estimate the effort required for synchronization."""
    if not items:
        return "none"

    create_count = len([item for item in items if item.action == SyncAction.CREATE])
    migrate_count = len([item for item in items if item.action == SyncAction.MIGRATE])
    update_count = len([item for item in items if item.action == SyncAction.UPDATE])

    if migrate_count > 0 or len(breaking_changes) > 2:
        return "high"
    elif update_count > 2 or create_count > 1:
        return "medium"
    else:
        return "low"


def preview_sync_plan(plan: SyncPlan) -> None:
    """Preview a sync plan without executing it."""
    if not plan.items:
        print("✅ Everything is already synchronized")
        return

    print(f"📋 Sync Plan ({len(plan.items)} items):")
    print(f"   Estimated effort: {plan.estimated_time}")
    print(
        f"   Manual review required: {'Yes' if plan.requires_manual_review else 'No'}"
    )

    if plan.breaking_changes:
        print(f"\n💥 Breaking Changes ({len(plan.breaking_changes)}):")
        for change in plan.breaking_changes[:5]:  # Show first 5
            print(f"   - {change}")
        if len(plan.breaking_changes) > 5:
            remaining = len(plan.breaking_changes) - 5
            print(f"   ... and {remaining} more")

    print("\n📋 Actions:")

    if plan.create_items:
        print(f"   🆕 Create ({len(plan.create_items)}):")
        for item in plan.create_items:
            print(f"      - {item.description}")

    if plan.update_items:
        print(f"   🔄 Update ({len(plan.update_items)}):")
        for item in plan.update_items:
            print(f"      - {item.description}")

    if plan.migrate_items:
        print(f"   ⚠️  Migrate ({len(plan.migrate_items)}):")
        for item in plan.migrate_items:
            print(f"      - {item.description}")

    if plan.delete_items:
        print(f"   🗑️  Delete ({len(plan.delete_items)}):")
        for item in plan.delete_items:
            print(f"      - {item.description}")

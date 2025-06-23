"""Version management commands for liveapi CLI."""

from ...version_manager import VersionManager, VersionType
from ..utils import resolve_spec_path, extract_spec_name_from_input


def cmd_version(args):
    """Manage API versions."""
    version_manager = VersionManager()

    if not args.version_action:
        print("❌ Version action required. Use: create, list, or compare")
        return

    if args.version_action == "create":
        cmd_version_create(args, version_manager)
    elif args.version_action == "list":
        cmd_version_list(args, version_manager)
    elif args.version_action == "compare":
        cmd_version_compare(args, version_manager)


def cmd_version_create(args, version_manager: VersionManager):
    """Create a new version of a specification."""
    spec_input = args.spec

    # Resolve spec path
    spec_path = resolve_spec_path(spec_input)
    if not spec_path:
        print(f"❌ Specification not found: {spec_input}")
        return

    # Convert version type string to enum
    version_type_map = {
        "major": VersionType.MAJOR,
        "minor": VersionType.MINOR,
        "patch": VersionType.PATCH,
        "auto": VersionType.AUTO,
    }
    version_type = version_type_map.get(args.version_type, VersionType.AUTO)

    try:
        print(f"🚀 Creating new version of {spec_path.name}...")

        if args.target:
            versioned_spec = version_manager.create_version(
                spec_path, target_version=args.target
            )
            print(
                f"✅ Created version {versioned_spec.version} (target: {args.target})"
            )
        else:
            versioned_spec = version_manager.create_version(spec_path, version_type)
            print(
                f"✅ Created version {versioned_spec.version} ({args.version_type} bump)"
            )

        print(f"📁 File: {versioned_spec.file_path}")
        print(
            f"🔗 Latest symlink updated: specifications/latest/{versioned_spec.name}.yaml"
        )

        # Show what changed if not first version
        versions = version_manager.get_spec_versions(versioned_spec.name)
        if len(versions) > 1:
            prev_version = versions[-2]  # Second to last
            try:
                analysis = version_manager.compare_versions(
                    versioned_spec.name,
                    str(prev_version.version),
                    str(versioned_spec.version),
                )
                print(f"\n📋 Changes from v{prev_version.version}:")
                for change in analysis.changes[:5]:  # Show first 5 changes
                    icon = "💥" if change.is_breaking else "📝"
                    print(f"   {icon} {change.description}")

                if len(analysis.changes) > 5:
                    remaining = len(analysis.changes) - 5
                    print(f"   ... and {remaining} more changes")

            except Exception:
                pass  # Skip comparison if it fails

    except Exception as e:
        print(f"❌ Failed to create version: {e}")


def cmd_version_list(args, version_manager: VersionManager):
    """List all versions of specifications."""
    if args.spec:
        # List versions for specific spec
        spec_name = extract_spec_name_from_input(args.spec)
        versions = version_manager.get_spec_versions(spec_name)

        if not versions:
            print(f"📋 No versions found for: {spec_name}")
            return

        print(f"📋 Versions of {spec_name}:")
        for version in versions:
            is_latest = "← latest" if version == versions[-1] else ""
            created = version.created_at[:10]  # Show just the date
            print(f"   v{version.version} ({created}) {is_latest}")
    else:
        # List all specs and their versions
        compatibility_matrix = version_manager.get_compatibility_matrix()

        if not compatibility_matrix:
            print("📋 No versioned specifications found")
            return

        print("📋 All specification versions:")
        for spec_name, versions in compatibility_matrix.items():
            latest_version = None
            version_count = len(versions)

            for version, info in versions.items():
                if info.get("is_latest"):
                    latest_version = version
                    break

            if latest_version:
                print(f"   {spec_name}: v{latest_version} ({version_count} versions)")
            else:
                print(f"   {spec_name}: ({version_count} versions)")


def cmd_version_compare(args, version_manager: VersionManager):
    """Compare two versions of a specification."""
    spec_name = extract_spec_name_from_input(args.spec)

    try:
        print(f"🔍 Comparing {spec_name} v{args.from_version} → v{args.to_version}")

        # Get comparison analysis
        analysis = version_manager.compare_versions(
            spec_name, args.from_version, args.to_version
        )

        if not analysis.changes:
            print("✅ No changes detected between versions")
            return

        print(f"\n📊 Summary: {analysis.summary}")

        # Show breaking changes
        if analysis.breaking_changes:
            print(f"\n💥 Breaking Changes ({len(analysis.breaking_changes)}):")
            for change in analysis.breaking_changes:
                print(f"   - {change.description}")

        # Show non-breaking changes
        if analysis.non_breaking_changes:
            print(f"\n📝 Non-Breaking Changes ({len(analysis.non_breaking_changes)}):")
            for change in analysis.non_breaking_changes[:10]:  # Limit to 10
                print(f"   - {change.description}")

            if len(analysis.non_breaking_changes) > 10:
                remaining = len(analysis.non_breaking_changes) - 10
                print(f"   ... and {remaining} more changes")

        # Generate migration plan
        migration_plan = version_manager.generate_migration_plan(
            spec_name, args.from_version, args.to_version
        )

        print("\n🔧 Migration Plan:")
        print(f"   Effort: {migration_plan.estimated_effort}")
        print(
            f"   Manual intervention: {'Yes' if migration_plan.requires_manual_intervention else 'No'}"
        )

        if migration_plan.migration_steps:
            print("\n📋 Migration Steps:")
            for i, step in enumerate(migration_plan.migration_steps, 1):
                print(f"   {i}. {step}")

    except Exception as e:
        print(f"❌ Comparison failed: {e}")

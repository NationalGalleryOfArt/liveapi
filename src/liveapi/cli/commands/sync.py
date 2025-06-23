"""Sync commands for liveapi CLI."""

import sys

from ...metadata_manager import MetadataManager, ProjectStatus
from ...sync_manager import SyncManager


def cmd_sync(args):
    """Sync implementations with specifications."""
    metadata_manager = MetadataManager()

    # Check project initialization
    status = metadata_manager.get_project_status()
    if status == ProjectStatus.UNINITIALIZED:
        print("❌ Project not initialized. Run 'liveapi init' first.")
        return

    sync_manager = SyncManager()

    print("🔍 Analyzing synchronization requirements...")

    try:
        # Analyze what needs to be synced
        sync_plan = sync_manager.analyze_sync_requirements()

        if not sync_plan.items:
            print("✅ Everything is already synchronized")
            return

        # Show preview if requested or if breaking changes require confirmation
        if args.preview:
            sync_manager._preview_sync_plan(sync_plan)
            return

        # Confirm breaking changes unless --force is used
        if sync_plan.requires_manual_review and not args.force:
            print("⚠️  Breaking changes detected!")
            sync_manager._preview_sync_plan(sync_plan)
            print()

            response = input("⚠️  Continue with synchronization? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("❌ Synchronization cancelled")
                return

        # Execute the sync plan
        print(f"\n🚀 Executing sync plan ({len(sync_plan.items)} items)...")
        success = sync_manager.execute_sync_plan(
            sync_plan,
            preview_only=False,
            use_scaffold=True,  # Always use scaffold mode
        )

        if success:
            print("✨ Synchronization completed successfully!")

            if sync_plan.requires_manual_review:
                print("\n📋 Next steps:")
                print("   1. Review generated migration guides (*.migration.md)")
                print("   2. Merge custom code from backups")
                print("   3. Test updated implementations")
                print("   4. Update any dependent code")
        else:
            print("⚠️  Synchronization completed with some issues")
            print("📋 Check the output above for details")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Synchronization failed: {e}")
        sys.exit(1)

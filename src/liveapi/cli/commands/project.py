"""Project management commands for liveapi CLI."""

import sys
from pathlib import Path

from ...metadata_manager import MetadataManager, ProjectStatus
from ...change_detector import ChangeDetector


def handle_no_command():
    """Handle when liveapi is run with no arguments."""
    metadata_manager = MetadataManager()
    status = metadata_manager.get_project_status()

    print("🚀 Welcome to LiveAPI!")
    print()

    if status == ProjectStatus.UNINITIALIZED:
        print("This directory is not yet a LiveAPI project.")
        print()
        print("What would you like to do?")
        print("1. Initialize a new project and generate an API spec")
        print("2. Initialize with existing OpenAPI specs")
        print("3. Show help")
        print()

        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            # Initialize and generate
            print("\n🚀 Let's create your project!")
            project_name = input("Project name (default: directory name): ").strip()

            # Create args object for init
            class Args:
                name = project_name or None

            cmd_init(Args())

            # API key is no longer required

            # Ask if they want to generate a spec
            print("\n✨ Would you like to generate an OpenAPI specification now?")
            response = input("Generate spec? (Y/n): ").strip().lower()

            if response != "n":
                # Create args for generate
                class GenArgs:
                    output = None
                    format = "yaml"

                from .generate import cmd_generate

                cmd_generate(GenArgs())

                # Offer to sync after successful generation
                print("\n✨ Would you like to generate implementation files now?")
                sync_response = (
                    input("Generate implementations? (Y/n): ").strip().lower()
                )

                if sync_response != "n":
                    from .sync import cmd_sync

                    # Create args for sync
                    class SyncArgs:
                        preview = False
                        force = False

                    cmd_sync(SyncArgs())

        elif choice == "2":
            # Just initialize
            class Args:
                name = None

            cmd_init(Args())

        else:
            print("\nRun 'liveapi --help' for usage information.")
    else:
        # Project is initialized, show status
        print("Your LiveAPI project is ready!")
        print()
        print("Quick actions:")
        print("  liveapi status    - Check for API changes")
        print("  liveapi generate  - Generate a new API spec")
        print("  ls .liveapi/prompts/ - View saved prompts and schemas")
        print("  liveapi sync      - Sync implementations with specs")
        print("  liveapi run       - Start development server")
        print("  liveapi --help    - Show all commands")
        print()

        # Show brief status
        change_detector = ChangeDetector()
        all_changes = change_detector.detect_all_changes()

        if all_changes:
            print(f"📋 {len(all_changes)} specification(s) have pending changes")
            print("Run 'liveapi status' for details")
        else:
            print("✅ All specifications are synchronized")


def cmd_init(args):
    """Initialize a new liveapi project."""
    metadata_manager = MetadataManager()

    # Check if already initialized
    status = metadata_manager.get_project_status()
    if status != ProjectStatus.UNINITIALIZED:
        print("⚠️  Project is already initialized")
        return

    project_name = args.name or Path.cwd().name
    print(f"🚀 Initializing liveapi project: {project_name}")

    # Prompt for API base URL
    api_base_url = None
    try:
        api_base_url = input(
            "🌐 API base URL (e.g., api.mycompany.com, optional): "
        ).strip()
        if not api_base_url:
            api_base_url = None
        elif api_base_url:
            # Remove protocol if user provided it
            if api_base_url.startswith("http://") or api_base_url.startswith(
                "https://"
            ):
                from urllib.parse import urlparse

                parsed = urlparse(api_base_url)
                api_base_url = parsed.netloc
                print(f"⚠️  Using domain: {api_base_url}")
    except (KeyboardInterrupt, EOFError):
        print("\n⚠️  Skipping API base URL setup")
        api_base_url = None

    # Initialize project
    metadata_manager.initialize_project(project_name, api_base_url)

    # Discover existing specs
    change_detector = ChangeDetector()
    specs = change_detector.find_api_specs()

    if specs:
        print(f"📋 Discovered {len(specs)} OpenAPI specification(s):")
        for spec in specs:
            print(f"   - {spec}")
            # Track each discovered spec
            change_detector.update_spec_tracking(spec)

        metadata_manager.update_last_sync()
        print("✅ Specifications tracked and project initialized")
    else:
        print("📋 No OpenAPI specifications found")
        print("💡 Add your .yaml or .json OpenAPI specs and run 'liveapi status'")

    print(f"✨ Project '{project_name}' initialized successfully!")
    print("📁 Created .liveapi/ directory for metadata")
    if api_base_url:
        print(f"🌐 API base URL configured: {api_base_url}")


def cmd_status(args):
    """Show project status and detect changes."""
    metadata_manager = MetadataManager()
    change_detector = ChangeDetector()

    # Check project initialization
    status = metadata_manager.get_project_status()
    if status == ProjectStatus.UNINITIALIZED:
        print("❌ Project not initialized. Run 'liveapi init' first.")
        if args.check:
            sys.exit(1)
        return

    # Load project config
    config = metadata_manager.load_config()
    print(f"📁 Project: {config.project_name}")
    print(f"📅 Created: {config.created_at}")
    if config.last_sync:
        print(f"🔄 Last sync: {config.last_sync}")
    if config.api_base_url:
        print(f"🌐 API Base URL: {config.api_base_url}")
    print()

    # Detect changes in all specs
    all_changes = change_detector.detect_all_changes()

    if not all_changes:
        print("✅ All specifications are up to date")
        print("🔄 No changes detected since last sync")
        return

    # Display changes
    print("📋 Changes detected:")
    has_breaking = False

    for spec_path, analysis in all_changes.items():
        spec_name = Path(spec_path).name

        if analysis.is_breaking:
            print(f"   ⚠️  {spec_name}: {analysis.summary}")
            has_breaking = True
        else:
            print(f"   ℹ️  {spec_name}: {analysis.summary}")

        # Show detailed changes
        for change in analysis.changes[:3]:  # Show first 3 changes
            icon = "💥" if change.is_breaking else "📝"
            print(f"      {icon} {change.description}")

        if len(analysis.changes) > 3:
            remaining = len(analysis.changes) - 3
            print(f"      ... and {remaining} more changes")
        print()

    # Summary
    total_specs = len(all_changes)
    breaking_specs = len([a for a in all_changes.values() if a.is_breaking])

    if has_breaking:
        print(
            f"⚠️  {breaking_specs} of {total_specs} specifications have breaking changes"
        )
        print("🔧 Run 'liveapi sync --preview' to see implementation impact")
    else:
        print(f"ℹ️  {total_specs} specifications have non-breaking changes")
        print("🔧 Run 'liveapi sync' to update implementations")

    # Exit with error code if --check flag is used and changes exist
    if args.check:
        sys.exit(1 if has_breaking else 0)


def cmd_validate(args):
    """Validate all OpenAPI specifications."""
    change_detector = ChangeDetector()

    specs = change_detector.find_api_specs()
    if not specs:
        print("📋 No OpenAPI specifications found")
        return

    print(f"🔍 Validating {len(specs)} specification(s)...")

    valid_count = 0
    error_count = 0

    for spec_path in specs:
        spec_name = spec_path.name
        try:
            # Try to load the spec
            spec_data = change_detector._load_spec(spec_path)

            # Basic validation
            if "openapi" not in spec_data and "swagger" not in spec_data:
                raise ValueError("Missing 'openapi' or 'swagger' field")

            if "info" not in spec_data:
                raise ValueError("Missing 'info' section")

            if "paths" not in spec_data:
                raise ValueError("Missing 'paths' section")

            print(f"   ✅ {spec_name}: Valid")
            valid_count += 1

        except Exception as e:
            print(f"   ❌ {spec_name}: {e}")
            error_count += 1

    print()
    if error_count == 0:
        print(f"✅ All {valid_count} specifications are valid")
    else:
        print(f"❌ {error_count} specification(s) have errors")
        print(f"✅ {valid_count} specification(s) are valid")
        sys.exit(1)

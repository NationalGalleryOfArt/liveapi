"""Main CLI entry point for liveapi."""

import sys
import argparse

from .commands.project import handle_no_command, cmd_init, cmd_status, cmd_validate
from .commands.version import cmd_version
from .commands.sync import cmd_sync
from .commands.generate import cmd_generate, cmd_regenerate
from .commands.server import cmd_run, cmd_kill, cmd_ping


def main():
    """Main CLI entry point for liveapi."""
    parser = argparse.ArgumentParser(
        description="LiveAPI - API Lifecycle Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  liveapi                         # Interactive mode
  liveapi init                    # Initialize new project
  liveapi generate                # Generate OpenAPI spec with AI
  liveapi regenerate prompt.json  # Regenerate spec from saved prompt
  liveapi status                  # Show project status
  liveapi validate                # Validate all specifications
  liveapi version users --major   # Create major version of users API
  liveapi version list users      # List all versions of users API
  liveapi sync                    # Generate individual implementation files
  liveapi run                     # Run FastAPI app with uvicorn --reload
  liveapi run --background        # Run in background with PID file
  liveapi kill                    # Stop background FastAPI app
  liveapi ping                    # Check local dev server health
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize liveapi project")
    init_parser.add_argument("--name", help="Project name (default: directory name)")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with non-zero code if changes detected",
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate all specifications"
    )
    validate_parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix validation issues"
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Manage API versions")
    version_subparsers = version_parser.add_subparsers(
        dest="version_action", help="Version actions"
    )

    # Version create
    version_create_parser = version_subparsers.add_parser(
        "create", help="Create new version"
    )
    version_create_parser.add_argument("spec", help="Specification name or path")
    version_create_parser.add_argument(
        "--major",
        action="store_const",
        dest="version_type",
        const="major",
        help="Create major version",
    )
    version_create_parser.add_argument(
        "--minor",
        action="store_const",
        dest="version_type",
        const="minor",
        help="Create minor version",
    )
    version_create_parser.add_argument(
        "--patch",
        action="store_const",
        dest="version_type",
        const="patch",
        help="Create patch version",
    )
    version_create_parser.add_argument(
        "--auto",
        action="store_const",
        dest="version_type",
        const="auto",
        default="auto",
        help="Auto-determine version type",
    )
    version_create_parser.add_argument(
        "--target", help="Specific version (e.g., 2.1.0)"
    )

    # Version list
    version_list_parser = version_subparsers.add_parser(
        "list", help="List all versions"
    )
    version_list_parser.add_argument(
        "spec", nargs="?", help="Specification name (optional)"
    )

    # Version compare
    version_compare_parser = version_subparsers.add_parser(
        "compare", help="Compare two versions"
    )
    version_compare_parser.add_argument("spec", help="Specification name")
    version_compare_parser.add_argument(
        "from_version", help="From version (e.g., 1.0.0)"
    )
    version_compare_parser.add_argument("to_version", help="To version (e.g., 2.0.0)")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync implementations with specs")
    sync_parser.add_argument(
        "--preview", action="store_true", help="Preview changes without applying them"
    )
    sync_parser.add_argument(
        "--force", action="store_true", help="Force sync even with breaking changes"
    )
    sync_parser.add_argument(
        "spec", nargs="?", help="Sync specific specification (optional)"
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate OpenAPI specification"
    )
    generate_parser.add_argument(
        "--output", "-o", help="Output file path (default: generated_api.yaml)"
    )
    generate_parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)",
    )

    # Regenerate command
    regenerate_parser = subparsers.add_parser(
        "regenerate", help="Regenerate API spec from saved prompt"
    )
    regenerate_parser.add_argument(
        "prompt_file", help="Path to saved prompt file (.liveapi/prompts/*.json)"
    )
    regenerate_parser.add_argument(
        "--output", "-o", help="Output file path (default: updates original spec)"
    )
    regenerate_parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format (default: yaml)",
    )

    # Run command
    run_parser = subparsers.add_parser(
        "run", help="Run the FastAPI application with uvicorn"
    )
    run_parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    run_parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    run_parser.add_argument(
        "--app",
        default="main:app",
        help="Application module and variable (default: main:app)",
    )
    run_parser.add_argument(
        "--no-reload", action="store_true", help="Disable auto-reload"
    )
    run_parser.add_argument(
        "--background",
        "-d",
        action="store_true",
        help="Run in background (daemon mode)",
    )
    run_parser.add_argument(
        "--pid-file", help="Custom PID file path (default: .liveapi/uvicorn.pid)"
    )

    # Kill command
    kill_parser = subparsers.add_parser(
        "kill", help="Stop the background FastAPI application"
    )
    kill_parser.add_argument(
        "--pid-file", help="Custom PID file path (default: .liveapi/uvicorn.pid)"
    )

    # Ping command
    ping_parser = subparsers.add_parser(
        "ping", help="Check health of local development server"
    )
    ping_parser.add_argument(
        "--pid-file", help="Custom PID file path (default: .liveapi/uvicorn.pid)"
    )

    args = parser.parse_args()

    if not args.command:
        # When no command is provided, offer interactive experience
        handle_no_command()
        return

    try:
        if args.command == "init":
            cmd_init(args)
        elif args.command == "status":
            cmd_status(args)
        elif args.command == "validate":
            cmd_validate(args)
        elif args.command == "version":
            cmd_version(args)
        elif args.command == "sync":
            cmd_sync(args)
        elif args.command == "generate":
            cmd_generate(args)
        elif args.command == "regenerate":
            cmd_regenerate(args)
        elif args.command == "run":
            cmd_run(args)
        elif args.command == "kill":
            cmd_kill(args)
        elif args.command == "ping":
            cmd_ping(args)
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

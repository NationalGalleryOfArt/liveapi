"""Command line interface for automatic."""

import sys
import argparse
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .scaffold import ScaffoldGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automatic - Runtime OpenAPI to FastAPI framework"
    )

    parser.add_argument(
        "spec_path",
        nargs="?",  # Make spec_path optional
        help="Path to OpenAPI specification file (if not provided, auto-discovers specs)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: auto-generated in implementations/ directory)",
        default=None,
    )

    args = parser.parse_args()

    if args.spec_path:
        # Single spec mode
        generate_scaffold(args.spec_path, args.output)
    else:
        # Auto-discovery mode
        auto_discover_and_setup()


def generate_scaffold(spec_path: str, output_path: str = None):
    """Generate implementation scaffold from OpenAPI spec."""
    try:
        generator = ScaffoldGenerator(spec_path)

        # Auto-generate output path if not provided
        if output_path is None:
            output_path = generator.get_default_output_path()

        success = generator.generate_scaffold(output_path)
        if success:
            print(f"✅ Scaffold generated: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def auto_discover_and_setup():
    """Auto-discover API specs and set up project structure."""
    current_dir = Path(".")

    # Check if we have existing project structure
    specifications_dir = current_dir / "specifications"
    implementations_dir = current_dir / "implementations"

    # Incremental mode: both directories exist (even if empty)
    if specifications_dir.exists() and implementations_dir.exists():
        # Incremental mode - add missing implementations
        print("🔍 Checking for new API specifications...")
        missing_implementations = find_missing_implementations()

        if not missing_implementations:
            print("✅ All specifications have corresponding implementations.")
            return

        print(
            f"📋 Found {len(missing_implementations)} specification(s) without implementations:"
        )
        for spec_file in missing_implementations:
            print(f"   - {spec_file}")

        # Add missing implementations
        add_missing_implementations(missing_implementations)

    else:
        # First run - look for all specs in current directory
        print("🔍 Looking for OpenAPI specifications in current directory...")
        spec_files = find_api_specs(current_dir)

        if not spec_files:
            print("❌ No OpenAPI specification files found in current directory.")
            print(
                "💡 Place your .yaml or .json OpenAPI specs here and run 'automatic' again."
            )
            return

        print(f"📋 Found {len(spec_files)} specification(s):")
        for spec_file in spec_files:
            print(f"   - {spec_file}")

        # Set up complete project for each spec
        setup_first_run(spec_files)


def find_api_specs(directory: Path) -> list[Path]:
    """Find all OpenAPI specification files in a directory."""
    spec_files = []

    # Look for YAML and JSON files that might be OpenAPI specs
    for pattern in ["*.yaml", "*.yml", "*.json"]:
        for file_path in directory.glob(pattern):
            if file_path.is_file() and is_openapi_spec(file_path):
                # Validate the spec early to catch common issues
                validate_spec_paths(file_path)
                spec_files.append(file_path)

    return sorted(spec_files)


def is_openapi_spec(file_path: Path) -> bool:
    """Check if a file appears to be an OpenAPI specification."""
    try:
        content = file_path.read_text()
        # Simple heuristic - look for OpenAPI indicators
        openapi_indicators = ["openapi:", "swagger:", '"openapi":', '"swagger":']
        return any(indicator in content.lower() for indicator in openapi_indicators)
    except Exception:
        return False


def validate_spec_paths(file_path: Path) -> None:
    """Validate OpenAPI spec for common issues early in the discovery process."""
    try:
        import yaml
        import json

        content = file_path.read_text()

        # Try to parse as YAML first, then JSON
        try:
            data = yaml.safe_load(content)
        except Exception:
            try:
                data = json.loads(content)
            except Exception:
                return  # If we can't parse it, skip validation

        # Check for root path mounting
        paths = data.get("paths", {})
        if "/" in paths:
            print(f"❌ Error in {file_path.name}:")
            print("   Cannot mount API at root path '/'.")
            print("   Use a specific resource path like '/users', '/locations', etc.")
            print("   Root path mounting is not supported for proper REST API design.")
            raise SystemExit(1)

        # Check for conflicting paths (paths that would overlap in routing)
        path_conflicts = _check_path_conflicts(list(paths.keys()))
        if path_conflicts:
            print(f"❌ Error in {file_path.name}:")
            print("   Conflicting paths detected:")
            for conflict in path_conflicts:
                print(f"   - {conflict}")
            print("   Conflicting paths can cause routing ambiguity.")
            print("   Use distinct resource paths that don't overlap.")
            raise SystemExit(1)

    except SystemExit:
        raise  # Re-raise system exit
    except Exception:
        # If validation fails for any reason, just continue
        # The full parser will catch any other issues later
        pass


def _check_path_conflicts(paths: list[str]) -> list[str]:
    """Check for conflicting paths that could cause routing ambiguity.

    Returns:
        List of conflict descriptions
    """
    conflicts = []

    for i, path1 in enumerate(paths):
        for j, path2 in enumerate(paths[i + 1 :], i + 1):
            # Check for various types of conflicts

            # 1. Exact duplicates
            if path1 == path2:
                conflicts.append(f"Duplicate paths: {path1}")
                continue

            # 2. One path is a prefix of another (except with parameters)
            # /users vs /users/profile would conflict
            if _paths_conflict(path1, path2):
                conflicts.append(f"Conflicting paths: '{path1}' and '{path2}'")

    return conflicts


def _paths_conflict(path1: str, path2: str) -> bool:
    """Check if two paths would conflict in FastAPI routing."""
    # Normalize paths (remove trailing slashes)
    p1 = path1.rstrip("/")
    p2 = path2.rstrip("/")

    # Split into segments
    seg1 = [s for s in p1.split("/") if s]
    seg2 = [s for s in p2.split("/") if s]

    # Standard REST patterns are allowed:
    # /users (collection) and /users/{id} (item) should NOT conflict
    if len(seg1) == len(seg2) + 1 or len(seg2) == len(seg1) + 1:
        # One is one segment longer - check if it's a parameter
        shorter, longer = (seg1, seg2) if len(seg1) < len(seg2) else (seg2, seg1)

        # Check if all segments of shorter path match longer path
        for i, seg in enumerate(shorter):
            if seg != longer[i]:
                break
        else:
            # All segments matched, check if extra segment is a parameter
            extra_seg = longer[len(shorter)]
            if extra_seg.startswith("{") and extra_seg.endswith("}"):
                return False  # Standard REST pattern - not a conflict

    # Check for actual conflicts
    min_len = min(len(seg1), len(seg2))

    for i in range(min_len):
        s1, s2 = seg1[i], seg2[i]

        # Both are parameters - they match
        if s1.startswith("{") and s2.startswith("{"):
            continue
        # One is parameter, one is literal at same position - conflict!
        elif s1.startswith("{") or s2.startswith("{"):
            return True
        # Both are literals - must match exactly
        elif s1 != s2:
            return False

    # If we get here and lengths are different, check for problematic prefix patterns
    if len(seg1) != len(seg2):
        # /users vs /users/profile (both literals) would be a conflict
        # But /users vs /users/{id} is OK (handled above)
        return True

    return False


def setup_first_run(spec_files: list[Path]):
    """Set up complete project structure for first run."""
    print("🚀 Setting up complete project structure...")

    # Determine if we're dealing with multiple specs
    is_multi_spec = len(spec_files) > 1

    # Process each spec file
    for i, spec_file in enumerate(spec_files):
        print(f"\n📝 Processing {spec_file.name} ({i + 1}/{len(spec_files)})...")

        try:
            generator = ScaffoldGenerator(str(spec_file))
            output_path = generator.get_default_output_path()

            # For multi-spec setups, we'll create the project structure manually
            # to avoid each scaffold trying to create its own main.py
            if is_multi_spec:
                # Temporarily disable project init for individual scaffolds
                generator._should_init_project = lambda: False

            success = generator.generate_scaffold(output_path)
            if success:
                print(f"   ✅ Created: {output_path}")
            else:
                print(f"   ❌ Skipped: {spec_file.name}")
        except Exception as e:
            print(f"   ❌ Error processing {spec_file.name}: {e}")

    # For multi-spec, create main.py and organize specs
    if is_multi_spec:
        # Organize all spec files and get their new paths
        organized_spec_paths = organize_spec_files(spec_files)
        # Create main.py that imports all implementations
        create_multi_spec_main(organized_spec_paths)
        # Create .gitignore if needed
        create_gitignore_if_needed()

    print("\n✨ Project setup complete!")
    print("🚀 Run with: python main.py")


def files_are_different(file1: Path, file2: Path) -> bool:
    """Compare two files to see if their content is different."""
    try:
        # Read and normalize content (strip whitespace, normalize line endings)
        content1 = file1.read_text().strip().replace("\r\n", "\n")
        content2 = file2.read_text().strip().replace("\r\n", "\n")
        return content1 != content2
    except Exception:
        # If we can't read one of the files, assume they're different
        return True


def find_missing_implementations() -> list[Path]:
    """Find specifications that don't have corresponding implementations."""
    specifications_dir = Path("specifications")

    if not specifications_dir.exists():
        return []

    missing = []

    for spec_file in specifications_dir.glob("*.yaml"):
        # Generate expected implementation filename
        generator = ScaffoldGenerator(str(spec_file))
        expected_impl_path = Path(generator.get_default_output_path())

        if not expected_impl_path.exists():
            missing.append(spec_file)

    for spec_file in specifications_dir.glob("*.yml"):
        generator = ScaffoldGenerator(str(spec_file))
        expected_impl_path = Path(generator.get_default_output_path())

        if not expected_impl_path.exists():
            missing.append(spec_file)

    return sorted(missing)


def add_missing_implementations(spec_files: list[Path]):
    """Add implementations for specifications that don't have them."""
    print("🚀 Adding missing implementations...")

    for spec_file in spec_files:
        print(f"\n📝 Creating implementation for {spec_file.name}...")

        try:
            generator = ScaffoldGenerator(str(spec_file))
            output_path = generator.get_default_output_path()

            success = generator.generate_scaffold(output_path)
            if success:
                print(f"   ✅ Created: {output_path}")
            else:
                print(f"   ❌ Skipped: {spec_file.name}")
        except Exception as e:
            print(f"   ❌ Error processing {spec_file.name}: {e}")

    print("\n✅ Implementation sync complete!")


def organize_spec_files(spec_files: list[Path]) -> list[Path]:
    """Move spec files to specifications/ directory with versioning.

    Returns:
        List of new organized file paths
    """
    specs_dir = Path("specifications")
    specs_dir.mkdir(exist_ok=True)

    import shutil

    organized_paths = []

    for spec_file in spec_files:
        # Only move if not already in specifications/
        if spec_file.parent != specs_dir:
            # Extract base name without extension
            base_name = spec_file.stem
            extension = spec_file.suffix

            # Check if this is already a versioned file (ends with _v{number})
            import re

            version_match = re.match(r"^(.+?)(_v\d+)?$", base_name)
            if version_match:
                base_name_without_version = version_match.group(1)
            else:
                base_name_without_version = base_name

            # Look for existing versions in specifications directory
            existing_versions = []
            for existing_file in specs_dir.glob(
                f"{base_name_without_version}_v*{extension}"
            ):
                # Extract version number
                existing_match = re.match(
                    rf"^{re.escape(base_name_without_version)}_v(\d+)$",
                    existing_file.stem,
                )
                if existing_match:
                    existing_versions.append(int(existing_match.group(1)))

            # If no versions exist, start with v1
            if not existing_versions:
                new_filename = f"{base_name_without_version}_v1{extension}"
                new_path = specs_dir / new_filename
            else:
                # Check if the file content is different from the highest version
                highest_version = max(existing_versions)
                highest_version_path = (
                    specs_dir
                    / f"{base_name_without_version}_v{highest_version}{extension}"
                )

                # Compare file contents
                if files_are_different(spec_file, highest_version_path):
                    # Create new version
                    new_version = highest_version + 1
                    new_filename = (
                        f"{base_name_without_version}_v{new_version}{extension}"
                    )
                    new_path = specs_dir / new_filename
                else:
                    # File is the same, skip moving
                    print(
                        f"   ℹ️  {spec_file.name} is identical to existing version, skipping"
                    )
                    # Use the existing version
                    organized_paths.append(highest_version_path)
                    continue

            # Move the file
            shutil.move(str(spec_file), str(new_path))
            print(f"   ✅ Moved {spec_file.name} → {new_path.name}")
            organized_paths.append(new_path)
        else:
            # File is already in specifications directory, use as-is
            organized_paths.append(spec_file)

    return organized_paths


def create_gitignore_if_needed():
    """Create .gitignore if it doesn't exist."""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
"""
        gitignore_path.write_text(gitignore_content)


def create_multi_spec_main(spec_files: list[Path]):
    """Create main.py that can handle multiple API specifications."""
    if len(spec_files) == 1:
        # Single spec - the individual scaffold process already created main.py
        return

    print("\n📝 Creating main.py for multiple APIs...")

    # Set up Jinja environment
    template_dir = Path(__file__).parent / "templates"
    jinja_env = Environment(
        loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True
    )

    # Add custom filters
    def to_snake_case(name: str) -> str:
        """Convert CamelCase to snake_case for use in Jinja templates."""
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    jinja_env.filters["to_snake_case"] = to_snake_case

    # Prepare implementation data for template
    implementations = []

    for spec_file in spec_files:
        # Use the same logic as ScaffoldGenerator to ensure consistency
        scaffold_gen = ScaffoldGenerator(str(spec_file))
        routes = scaffold_gen.parser.get_routes()
        template_data = scaffold_gen._prepare_template_data(routes)
        class_name = template_data["class_name"]

        # Get filename using the same logic as scaffold
        filename = scaffold_gen._class_name_to_filename(class_name)
        module_path = f"implementations.{filename[:-3]}"  # Remove .py extension

        # Determine versioned spec path in specifications directory
        # Need to find the actual versioned filename after organize_spec_files() runs
        base_name = spec_file.stem
        version_match = re.match(r"^(.+?)(_v\d+)?$", base_name)
        if version_match:
            base_name_without_version = version_match.group(1)
        else:
            base_name_without_version = base_name

        # The file will be versioned as {base_name_without_version}_v1.yaml
        versioned_filename = f"{base_name_without_version}_v1{spec_file.suffix}"
        spec_path = f"specifications/{versioned_filename}"

        implementations.append(
            {
                "class_name": class_name,
                "module_path": module_path,
                "versioned_filename": versioned_filename,
                "spec_path": spec_path,
            }
        )

    # Render template
    template = jinja_env.get_template("multi_spec_main.py.j2")
    main_content = template.render(implementations=implementations)

    main_file = Path("main.py")
    if main_file.exists():
        response = input("⚠️  main.py already exists. Overwrite? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("❌ main.py creation skipped.")
            return

    main_file.write_text(main_content)
    print("   ✅ Created: main.py")


if __name__ == "__main__":
    main()

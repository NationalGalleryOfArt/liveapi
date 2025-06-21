"""Command line interface for automatic."""

import sys
import argparse
from pathlib import Path
from .scaffold import ScaffoldGenerator


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automatic - Runtime OpenAPI to FastAPI framework"
    )
    
    parser.add_argument(
        'spec_path',
        nargs='?',  # Make spec_path optional
        help='Path to OpenAPI specification file (if not provided, auto-discovers specs)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: auto-generated in implementations/ directory)',
        default=None
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
    current_dir = Path('.')
    
    # Check if we have existing project structure
    specifications_dir = current_dir / 'specifications'
    implementations_dir = current_dir / 'implementations'
    
    # Incremental mode: both directories exist (even if empty)
    if specifications_dir.exists() and implementations_dir.exists():
        # Incremental mode - add missing implementations
        print("🔍 Checking for new API specifications...")
        missing_implementations = find_missing_implementations()
        
        if not missing_implementations:
            print("✅ All specifications have corresponding implementations.")
            return
        
        print(f"📋 Found {len(missing_implementations)} specification(s) without implementations:")
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
            print("💡 Place your .yaml or .json OpenAPI specs here and run 'automatic' again.")
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
    for pattern in ['*.yaml', '*.yml', '*.json']:
        for file_path in directory.glob(pattern):
            if file_path.is_file() and is_openapi_spec(file_path):
                spec_files.append(file_path)
    
    return sorted(spec_files)


def is_openapi_spec(file_path: Path) -> bool:
    """Check if a file appears to be an OpenAPI specification."""
    try:
        content = file_path.read_text()
        # Simple heuristic - look for OpenAPI indicators
        openapi_indicators = ['openapi:', 'swagger:', '"openapi":', '"swagger":']
        return any(indicator in content.lower() for indicator in openapi_indicators)
    except Exception:
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
        # Organize all spec files
        organize_spec_files(spec_files)
        # Create main.py that imports all implementations
        create_multi_spec_main(spec_files)
        # Create .gitignore if needed
        create_gitignore_if_needed()
    
    print("\n✨ Project setup complete!")
    print("🚀 Run with: python main.py")


def files_are_different(file1: Path, file2: Path) -> bool:
    """Compare two files to see if their content is different."""
    try:
        # Read and normalize content (strip whitespace, normalize line endings)
        content1 = file1.read_text().strip().replace('\r\n', '\n')
        content2 = file2.read_text().strip().replace('\r\n', '\n')
        return content1 != content2
    except Exception:
        # If we can't read one of the files, assume they're different
        return True


def find_missing_implementations() -> list[Path]:
    """Find specifications that don't have corresponding implementations."""
    specifications_dir = Path('specifications')
    
    if not specifications_dir.exists():
        return []
    
    missing = []
    
    for spec_file in specifications_dir.glob('*.yaml'):
        # Generate expected implementation filename
        generator = ScaffoldGenerator(str(spec_file))
        expected_impl_path = Path(generator.get_default_output_path())
        
        if not expected_impl_path.exists():
            missing.append(spec_file)
    
    for spec_file in specifications_dir.glob('*.yml'):
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


def organize_spec_files(spec_files: list[Path]):
    """Move spec files to specifications/ directory with versioning."""
    specs_dir = Path('specifications')
    specs_dir.mkdir(exist_ok=True)
    
    import shutil
    
    for spec_file in spec_files:
        # Only move if not already in specifications/
        if spec_file.parent != specs_dir:
            # Extract base name without extension
            base_name = spec_file.stem
            extension = spec_file.suffix
            
            # Check if this is already a versioned file (ends with _v{number})
            import re
            version_match = re.match(r'^(.+?)(_v\d+)?$', base_name)
            if version_match:
                base_name_without_version = version_match.group(1)
            else:
                base_name_without_version = base_name
            
            # Look for existing versions in specifications directory
            existing_versions = []
            for existing_file in specs_dir.glob(f"{base_name_without_version}_v*{extension}"):
                # Extract version number
                existing_match = re.match(rf'^{re.escape(base_name_without_version)}_v(\d+)$', existing_file.stem)
                if existing_match:
                    existing_versions.append(int(existing_match.group(1)))
            
            # If no versions exist, start with v1
            if not existing_versions:
                new_filename = f"{base_name_without_version}_v1{extension}"
                new_path = specs_dir / new_filename
            else:
                # Check if the file content is different from the highest version
                highest_version = max(existing_versions)
                highest_version_path = specs_dir / f"{base_name_without_version}_v{highest_version}{extension}"
                
                # Compare file contents
                if files_are_different(spec_file, highest_version_path):
                    # Create new version
                    new_version = highest_version + 1
                    new_filename = f"{base_name_without_version}_v{new_version}{extension}"
                    new_path = specs_dir / new_filename
                else:
                    # File is the same, skip moving
                    print(f"   ℹ️  {spec_file.name} is identical to existing version, skipping")
                    continue
            
            # Move the file
            shutil.move(str(spec_file), str(new_path))
            print(f"   ✅ Moved {spec_file.name} → {new_path.name}")


def create_gitignore_if_needed():
    """Create .gitignore if it doesn't exist."""
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        gitignore_content = '''# Python
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
'''
        gitignore_path.write_text(gitignore_content)


def create_multi_spec_main(spec_files: list[Path]):
    """Create main.py that can handle multiple API specifications."""
    if len(spec_files) == 1:
        # Single spec - the individual scaffold process already created main.py
        return
    
    print("\n📝 Creating main.py for multiple APIs...")
    
    main_content = '''"""FastAPI application entry point with multiple APIs."""

import uvicorn
from automatic import create_app

# Import all implementations
'''
    
    # Add imports for each implementation - build from the original spec names
    import_lines = []
    app_lines = []
    
    for spec_file in spec_files:
        # Generate class name from the original spec file
        # This matches what the scaffold generator would create
        generator = ScaffoldGenerator.__new__(ScaffoldGenerator)  # Don't call __init__ yet
        generator.spec_path = spec_file  # Set the path
        
        # Extract class name using the same logic as the generator
        # Use just the filename stem without extension for resource name extraction
        stem = spec_file.stem  # users.yaml -> users
        resource_name = generator._extract_resource_name([stem], [])
        class_name = generator._get_class_name(resource_name)
        
        # Build module path
        filename = generator._class_name_to_filename(class_name)
        module_path = f"implementations.{filename[:-3]}"  # Remove .py extension
        
        import_lines.append(f"from {module_path} import {class_name}")
        
        # Determine versioned spec path in specifications directory
        # Need to find the actual versioned filename after organize_spec_files() runs
        base_name = spec_file.stem
        import re
        version_match = re.match(r'^(.+?)(_v\d+)?$', base_name)
        if version_match:
            base_name_without_version = version_match.group(1)
        else:
            base_name_without_version = base_name
        
        # The file will be versioned as {base_name_without_version}_v1.yaml
        versioned_filename = f"{base_name_without_version}_v1{spec_file.suffix}"
        spec_path = f"specifications/{versioned_filename}"
        
        app_lines.append(f'    # {versioned_filename}')
        app_lines.append(f'    {class_name.lower()}_app = create_app(')
        app_lines.append(f'        spec_path="{spec_path}",')
        app_lines.append(f'        implementation={class_name}()')
        app_lines.append('    )')
        app_lines.append('')
    
    main_content += '\n'.join(import_lines)
    main_content += '''


def main():
    """Create and configure all FastAPI applications."""
    # For multiple APIs, you'll need to choose one of these approaches:
    # 1. Run each API on different ports
    # 2. Mount APIs under different paths
    # 3. Combine them into a single API
    
    # Example: Create apps for each specification
'''
    main_content += '\n'.join(app_lines)
    main_content += '''    
    # For this example, we'll return the first app
    # Modify this section based on your needs
    return ''' + f'{import_lines[0].split()[-1].lower()}_app' + '''


# Create the app instance for deployment
app = main()

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
'''
    
    main_file = Path('main.py')
    if main_file.exists():
        response = input("⚠️  main.py already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ main.py creation skipped.")
            return
    
    main_file.write_text(main_content)
    print("   ✅ Created: main.py")


if __name__ == '__main__':
    main()
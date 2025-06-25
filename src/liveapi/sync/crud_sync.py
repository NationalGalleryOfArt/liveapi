"""CRUD-specific sync operations for LiveAPI."""

from pathlib import Path
from typing import List
from jinja2 import Environment, FileSystemLoader


def create_crud_main_py(spec_files: List[Path], project_root: Path) -> None:
    """Create main.py for CRUD+ APIs using Jinja2 template.

    Args:
        spec_files: List of OpenAPI specification files (YAML or JSON)
        project_root: Root directory of the project
    """
    main_py_path = project_root / "main.py"
    
    # Set up Jinja2 environment for templates
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("main.py.j2")

    if len(spec_files) == 1:
        # Single spec mode
        spec_path = spec_files[0]
        relative_spec = spec_path.relative_to(project_root)
        
        content = template.render(
            single_spec=True,
            spec_path=str(relative_spec)
        )
    else:
        # Multiple specs mode 
        relative_specs = [str(spec.relative_to(project_root)) for spec in spec_files]
        
        content = template.render(
            single_spec=False,
            spec_files=relative_specs
        )

    # Write the main.py file
    main_py_path.write_text(content)
    print(f"✅ Created: {main_py_path}")


def sync_crud_implementation(spec_file: Path, project_root: Path) -> bool:
    """Sync CRUD implementation for a specification.

    Since we're using dynamic CRUD handlers, there's no code to generate.
    This function just ensures the spec exists and is valid.

    Args:
        spec_file: Path to OpenAPI specification
        project_root: Root directory of the project

    Returns:
        True if sync was successful, False otherwise
    """
    if not spec_file.exists():
        print(f"❌ Spec file not found: {spec_file}")
        return False

    try:
        # Just validate that we can parse the spec
        from ..implementation.liveapi_parser import LiveAPIParser
        
        parser = LiveAPIParser(str(spec_file))
        parser.load_spec()
        
        # Identify CRUD resources
        resources = parser.identify_crud_resources()
        
        if resources:
            print(f"✅ CRUD+ sync successful for {spec_file.name}")
            print(f"   Found {len(resources)} CRUD+ resources: {', '.join(resources.keys())}")
        else:
            print(f"⚠️ No CRUD+ resources found in {spec_file.name}")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to sync {spec_file.name}: {e}")
        return False
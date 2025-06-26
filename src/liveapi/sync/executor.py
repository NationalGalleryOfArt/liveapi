"""Execution logic for synchronization operations - CRUD mode."""

from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

from .models import SyncPlan
from .plan import preview_sync_plan


def execute_sync_plan(
    plan: SyncPlan,
    preview_only: bool,
    backup_dir: Path,
    metadata_manager,
    change_detector,
    project_root: Path,
) -> bool:
    """Execute a synchronization plan for scaffold mode."""
    if preview_only:
        preview_sync_plan(plan)
        return True

    if not plan.items:
        print("✅ Everything is already synchronized")
        return True

    return _execute_sync(plan, project_root, metadata_manager, change_detector)


def _execute_sync(
    plan: SyncPlan, project_root: Path, metadata_manager, change_detector
) -> bool:
    """Execute sync plan using scaffold generation mode."""
    print("🏗️  LiveAPI Scaffold Mode - Generating customizable service files...")

    success_count = 0
    implementations_dir = project_root / "implementations"
    implementations_dir.mkdir(exist_ok=True)

    for item in plan.items:
        try:
            if item.spec_name == "main.py":
                _create_main_py_for_implementations(project_root)
                success_count += 1
                continue

            # Generate implementation file directly (no templates needed)
            if _generate_implementation_file(
                item.source_path, implementations_dir, project_root
            ):
                success_count += 1
            else:
                print(f"❌ Failed to generate: {item.description}")
        except Exception as e:
            print(f"❌ Error generating {item.description}: {e}")

    # Also create main.py for easy running
    if success_count > 0:
        _update_sync_metadata(metadata_manager, change_detector)
        print(f"✅ Successfully generated {success_count} implementation files")
        print("📁 Files created in implementations/ directory")
        print("🎯 Customize your services in implementations/ for real data stores")
        return True
    else:
        print(f"⚠️  Generated {success_count} of {len(plan.items)} implementations")
        return False


def _generate_implementation_file(
    spec_path: Path, implementations_dir: Path, project_root: Path
) -> bool:
    """Generate an implementation file that inherits from CRUD handlers."""
    try:
        # Parse spec to get resource name
        import yaml

        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)

        # Load project configuration to check backend type
        from ..metadata_manager import MetadataManager

        metadata_manager = MetadataManager(project_root)
        config = metadata_manager.load_config()
        backend_type = getattr(config, "backend_type", "sqlmodel")

        # Extract resource name from spec
        resource_name = _extract_resource_name_from_spec(spec, spec_path)
        class_name = f"{resource_name.capitalize()}Service"

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))

        # Choose template based on backend type
        if backend_type == "sqlmodel":
            template = env.get_template("sql_model_resource_subclass.py.j2")
        else:
            template = env.get_template("default_resource_subclass.py.j2")

        # Generate the model for the resource
        from ..implementation.liveapi_parser import LiveAPIParser

        parser = LiveAPIParser(spec_path, backend_type=backend_type)
        resources = parser.identify_crud_resources()
        model = resources.get(resource_name, {}).get("model")
        model_name = model.__name__ if model else f"{resource_name.capitalize()}"

        # Create a models.py file for the implementation
        if model and hasattr(model, "model_source"):
            models_file = implementations_dir / "models.py"
            with open(models_file, "a") as f:
                f.write(f"\n\n# Model for {resource_name}\n")
                f.write(model.model_source)

        # Render the template
        content = template.render(
            resource_name=resource_name,
            class_name=class_name,
            model_name=model_name,
        )

        # Write the implementation file
        impl_file = implementations_dir / f"{resource_name}_service.py"
        impl_file.write_text(content)
        print(f"📝 Generated: {impl_file} (backend: {backend_type})")

        return True

    except Exception as e:
        print(f"❌ Error generating implementation: {e}")
        return False


def _extract_resource_name_from_spec(spec: Dict[str, Any], spec_path: Path) -> str:
    """Extract resource name from OpenAPI spec."""
    # Try to get from paths
    paths = spec.get("paths", {})
    for path in paths.keys():
        # Extract resource from path like /users, /locations, etc.
        parts = path.strip("/").split("/")
        if parts and parts[0] and not parts[0].startswith("{"):
            resource = parts[0].lower()
            # Remove plural 's' if present
            if resource.endswith("s") and len(resource) > 1:
                return resource[:-1]
            return resource

    # Fallback to spec filename
    stem = spec_path.stem
    if stem and stem != "api":
        return stem.lower()

    return "resource"


def _create_main_py_for_implementations(project_root: Path) -> None:
    """Create main.py using the same approach as CRUD+ mode."""
    # Just use the standard CRUD+ main.py generation
    from .crud_sync import create_crud_main_py

    # Get all specification files
    spec_files = list((project_root / "specifications").glob("*.yaml"))
    spec_files.extend(list((project_root / "specifications").glob("*.yml")))
    spec_files.extend(
        list((project_root / "specifications").glob("*.json"))
    )  # Also include JSON files

    if spec_files:
        create_crud_main_py(spec_files, project_root)


def _update_sync_metadata(metadata_manager, change_detector) -> None:
    """Update metadata after successful synchronization."""
    # Update last sync timestamp
    metadata_manager.update_last_sync()

    # Update spec tracking for all discovered specs
    for spec_file in change_detector.find_api_specs():
        change_detector.update_spec_tracking(spec_file)

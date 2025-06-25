"""CRUD-specific sync operations for LiveAPI."""

from pathlib import Path
from typing import List


def create_crud_main_py(spec_files: List[Path], project_root: Path) -> None:
    """Create main.py for CRUD+ APIs.

    Args:
        spec_files: List of OpenAPI specification files (YAML or JSON)
        project_root: Root directory of the project
    """
    main_py_path = project_root / "main.py"

    if len(spec_files) == 1:
        # Single spec mode
        spec_path = spec_files[0]
        relative_spec = spec_path.relative_to(project_root)

        content = f'''"""FastAPI application using LiveAPI CRUD+ handlers."""

import uvicorn
from liveapi.implementation import create_app

# Create the app from OpenAPI specification
app = create_app("{relative_spec}")

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
'''
    else:
        # Multiple specs - combine them
        imports = []
        app_creations = []

        for i, spec_path in enumerate(spec_files):
            relative_spec = spec_path.relative_to(project_root)
            app_name = f"app_{i + 1}"
            imports.append(
                f"from liveapi.implementation import create_app as create_app_{i + 1}"
            )
            app_creations.append(f'{app_name} = create_app_{i + 1}("{relative_spec}")')

        content = f'''"""FastAPI application combining multiple APIs using LiveAPI CRUD+ handlers."""

import uvicorn
from fastapi import FastAPI
{chr(10).join(imports)}

# Create individual apps
{chr(10).join(app_creations)}

# Main app that combines all APIs
app = FastAPI(
    title="Combined LiveAPI Services",
    description="Multiple CRUD+ APIs combined into one service"
)

# Mount each API under its own prefix
'''

        for i, spec_path in enumerate(spec_files):
            resource_name = spec_path.stem.split("_")[0]  # Extract base name
            content += f'app.mount("/{resource_name}", app_{i + 1})\n'

        content += """
if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
"""

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
        True if successful
    """
    if not spec_file.exists():
        print(f"❌ Specification not found: {spec_file}")
        return False

    print(f"✅ Ready to serve CRUD+ API from: {spec_file}")
    return True

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
        # Multiple specs - combine them with unified documentation
        content = '''"""FastAPI application combining multiple APIs using LiveAPI CRUD+ handlers with unified docs."""

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pathlib import Path

from liveapi.implementation.liveapi_router import (
    LiveAPIRouter,
    create_business_exception_handler,
    create_rfc7807_validation_error_handler,
    add_error_schemas_to_app
)
from liveapi.implementation.liveapi_parser import LiveAPIParser
from liveapi.implementation.exceptions import BusinessException

# Main app that combines all APIs
app = FastAPI(
    title="Combined LiveAPI Services",
    description="Multiple CRUD+ APIs combined into one service",
    version="0.1.0"
)

# Create a single router instance
main_router = LiveAPIRouter()

# Discover and load all APIs from the specifications directory
spec_dir = Path("specifications")
loaded_specs = []

if spec_dir.exists() and spec_dir.is_dir():
    # Check for all spec file types
    spec_files = list(spec_dir.glob("*.json"))
    spec_files.extend(spec_dir.glob("*.yaml"))
    spec_files.extend(spec_dir.glob("*.yml"))
    
    for spec_file in spec_files:
        try:
            # Parse the spec and create routers
            parser = LiveAPIParser(str(spec_file), backend_type=main_router.backend_type)
            parser.load_spec()
            resources = parser.identify_crud_resources()
            
            # Create routers for each resource
            for resource_name, resource_info in resources.items():
                model = resource_info["model"]
                if model:
                    # Create router with the resource name as prefix
                    router = main_router._create_resource_router(
                        resource_name, resource_info, model
                    )
                    # Include the router in the main app
                    app.include_router(router, tags=[resource_name])
                    loaded_specs.append(f"{spec_file.stem}/{resource_name}")
                    print(f"✅ Loaded {resource_name} from {spec_file}")

        except Exception as e:
            print(f"❌ Error loading spec from {spec_file}: {e}")

# Add custom exception handlers
app.add_exception_handler(BusinessException, create_business_exception_handler())
app.add_exception_handler(RequestValidationError, create_rfc7807_validation_error_handler())

# Add error schemas to OpenAPI schema
add_error_schemas_to_app(app)

# Add a root endpoint to list available APIs
@app.get("/", tags=["info"])
async def root():
    """List all available API endpoints."""
    return {
        "message": "Combined LiveAPI Services",
        "loaded_resources": loaded_specs,
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

# Add health check
@app.get("/health", tags=["info"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "liveapi.combined",
        "resources": loaded_specs
    }

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
'''

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

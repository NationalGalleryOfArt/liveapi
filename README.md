# LiveAPI

**A Python framework for generating and serving REST APIs from OpenAPI specifications.**

LiveAPI combines interactive spec generation, immutable versioning, change detection, and a default resource service to provide instant, standardized APIs from OpenAPI specifications.

## Features

### 🤖 Interactive Spec Generation
- **Interactive Generation**: Interactively generate OpenAPI specifications from high-level prompts.
- **Schema-First Workflow**: Start with a simple JSON schema for your objects; LiveAPI infers the rest.
- **Editable Intermediates**: Edit the generated JSON schema directly for fine-grained control.
- **Smart Regeneration**: Automatically rebuilds specs from edited schemas.
- **Standards Compliant**: Generates OpenAPI 3.0 specs with professional error handling (RFC 7807).
- **Visual Designer**: Browser-based UI for designing APIs with real-time preview (run `liveapi designer`).

### 🚀 Pluggable & Database-Ready Implementation
- **Selectable Backends**: Choose your data backend during project generation—from a simple in-memory store for prototypes to a production-ready SQL database with SQLModel.
- **Pluggable Service Architecture**: The API layer is decoupled from the data layer, allowing for easy extension with other databases like Redis or Elasticsearch.
- **Customizable Service Classes**: Generates clean, database-ready service classes with clear method overrides for your business logic.
- **Business Logic Hooks**: Built-in spots for validation, logging, caching, and event publishing.
- **Professional Error Handling**: RFC 7807 compliant error responses with proper exception handling.

### 🔄 API Lifecycle Management
- **Immutable Versioning**: Specs are versioned and become read-only (e.g., `users.yaml` → `users_v1.0.0.yaml`).
- **Change Detection**: SHA256-based tracking with breaking vs. non-breaking analysis.
- **Implementation Sync**: Keep your `main.py` synchronized with spec changes.
- **Migration Planning**: Automated guides with effort estimation for updates.

### 🛡️ Safe Evolution
- **Preview Mode**: See changes before applying them.
- **Automatic Backups**: Rollback capability for all changes.
- **Git Integration**: Version control ready, with a shared `.liveapi/` metadata directory for teams.

## How It Works

LiveAPI simplifies API creation from spec to running server. You can use the interactive CLI or the visual designer to create your API specifications, then generate implementation files and run your API server.

### Visual Designer

The LiveAPI Designer provides a browser-based interface for designing APIs:

1. Run `liveapi designer` to launch the designer in your browser
2. Edit the JSON in the left panel to define your API
3. Click "Generate API" to create the OpenAPI specification
4. See the preview update in real-time on the right panel

![LiveAPI Designer](https://example.com/liveapi-designer.png)
## Usage

```bash
# 1. Generate a new API spec interactively
liveapi generate
# Object name: > users
# JSON schema: {"name": "string", "email": "string", "active": "boolean"}
# JSON array examples: [{"name": "Alice", "email": "alice@example.com", "active": true}]
# 💾 Prompt saved to: .liveapi/prompts/users_prompt.json
# 📋 Schema saved to: .liveapi/prompts/users_schema.json

# 2. (Optional) Edit the clean JSON schema
# open .liveapi/prompts/users_schema.json

# 3. Check status
liveapi status
# ✅ Users API: ready for sync

# 4. Sync to generate customizable implementation files
liveapi sync
# ✅ Created: implementations/users_service.py (with database hooks)
# ✅ Created: main.py

# 5. Run your API immediately
liveapi run
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# Test with: curl http://localhost:8000/users
# DELETE: curl -X DELETE http://localhost:8000/users/1

# 6. Manage the development server
liveapi ping                   # Check server health
liveapi kill                   # Stop development server
```

## Quick Start

For a detailed getting started guide, see [QUICKSTART.md](QUICKSTART.md).

**Quick setup:**
```bash
# Install LiveAPI
git clone <repository-url>
cd liveapi
pip install -e .

# Create project directory
mkdir my-api-project && cd my-api-project

# Run interactive mode (handles init, generate, sync)
liveapi

# Start API server
liveapi run
```

## CRUD Operations

Generated APIs provide standard CRUD operations:

```bash
# Create
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "active": true}'

# Read
curl http://localhost:8000/users/123

# Update
curl -X PUT http://localhost:8000/users/123 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "email": "alice@example.com", "active": true}'

# Delete
curl -X DELETE http://localhost:8000/users/123

# List
curl "http://localhost:8000/users?limit=10&offset=0"

# Invalid data returns an RFC 7807 error response
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
# Returns: {"title": "Unprocessable Entity", "detail": "...", "status": "422"}
```

## Generated Implementation Files

The `liveapi sync` command generates a clean, customizable service class that is ready for you to connect to your database of choice.

#### Example: `implementations/users_service.py` (SQLModel Backend)

```python
# implementations/users_service.py (auto-generated for SQLModel)
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from liveapi.implementation.database import engine
from liveapi.implementation.exceptions import NotFoundError, ValidationError, ConflictError
from .models import User


class UserService:
    """Service for user resources."""

    def __init__(self):
        self.session = Session(engine)

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new resource."""
        try:
            resource_data = data.copy()
            
            resource_id = resource_data.get("id")
            if not resource_id:
                resource_id = str(uuid.uuid4())
                resource_data["id"] = resource_id

            now = datetime.now(timezone.utc)
            if hasattr(User, 'created_at'):
                resource_data["created_at"] = now
            if hasattr(User, 'updated_at'):
                resource_data["updated_at"] = now

            db_resource = User(**resource_data)
            
            existing = self.session.get(User, resource_id)
            if existing:
                raise ConflictError(
                    f"user with ID {resource_id} already exists"
                )
            
            self.session.add(db_resource)
            self.session.commit()
            self.session.refresh(db_resource)
            
            return db_resource.model_dump(mode="json")
                
        except IntegrityError as e:
            raise ConflictError(f"Database constraint violation: {str(e)}")
        except Exception as e:
            if isinstance(e, (ConflictError, ValidationError)):
                raise
            raise ValidationError(f"Invalid data: {str(e)}")

    async def read(self, resource_id: str) -> Dict[str, Any]:
        """Read a single resource by ID."""
        db_resource = self.session.get(User, resource_id)
        if not db_resource:
            raise NotFoundError(
                f"user with ID {resource_id} not found"
            )
        
        return db_resource.model_dump(mode="json")

    async def update(
        self, resource_id: str, data: Dict[str, Any], partial: bool = False
    ) -> Dict[str, Any]:
        """Update an existing resource."""
        db_resource = self.session.get(User, resource_id)
        if not db_resource:
            raise NotFoundError(
                f"user with ID {resource_id} not found"
            )

        try:
            update_data = data.copy()
            
            if partial:
                for key, value in update_data.items():
                    if hasattr(db_resource, key):
                        setattr(db_resource, key, value)
            else:
                existing_dict = db_resource.model_dump(mode="json")
                
                update_data["id"] = resource_id
                if "created_at" in existing_dict:
                    update_data["created_at"] = existing_dict["created_at"]
                
                for key, value in update_data.items():
                    if hasattr(db_resource, key):
                        setattr(db_resource, key, value)

            if hasattr(db_resource, 'updated_at'):
                db_resource.updated_at = datetime.now(timezone.utc)

            self.session.add(db_resource)
            self.session.commit()
            self.session.refresh(db_resource)
            
            return db_resource.model_dump(mode="json")
            
        except Exception as e:
            self.session.rollback()
            raise ValidationError(f"Invalid data: {str(e)}")

    async def delete(self, resource_id: str) -> None:
        """Delete a resource."""
        db_resource = self.session.get(User, resource_id)
        if not db_resource:
            raise NotFoundError(
                f"user with ID {resource_id} not found"
            )

        self.session.delete(db_resource)
        self.session.commit()

    async def list(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> List[Dict[str, Any]]:
        """List resources."""
        query = select(User)
        
        if filters:
            from .utils import apply_filters
            query = apply_filters(query, User, filters)
        
        query = query.offset(offset).limit(limit)
        
        results = self.session.exec(query).all()
        
        return [resource.model_dump(mode="json") for resource in results]
```

### Main Application
```python
# main.py (auto-generated)
"""Main application file for the FastAPI server."""

from fastapi import FastAPI
from liveapi.implementation.app import create_app
import os

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the specification file
spec_path = os.path.join(current_dir, "specifications", "users.yaml")

app = create_app(spec_path=spec_path)

@app.get("/")
def read_root():
    return {"message": "Welcome to the LiveAPI!"}

```

## Command Reference

### Project Management
```bash
liveapi init                   # Initialize project
liveapi generate               # Generate OpenAPI spec interactively
liveapi status                 # Show changes and sync status
liveapi validate               # Validate OpenAPI specs
liveapi designer               # Launch the LiveAPI Designer UI
```

### Development Server
```bash
liveapi run                    # Start development server (foreground)
liveapi run --background       # Start in background with PID file
liveapi run --port 3000        # Custom port
liveapi ping                   # Health check local server
liveapi kill                   # Stop background server
```

### Version Control
```bash
liveapi version create         # Auto-detect version type (major, minor, patch)
liveapi version create --major # Force a major version
liveapi version create --minor # Force a minor version
liveapi version create --patch # Force a patch version
liveapi version list           # List all versions
liveapi version compare v1 v2  # Compare two versions
```

### Synchronization
```bash
liveapi sync                  # Generate implementation files
liveapi sync --preview        # Preview changes without applying
liveapi sync --force          # Force sync without confirmation
```

## Project Structure

After initialization and sync:
```
my-api-project/
├── .liveapi/
│   ├── config.json              # Project configuration
│   ├── specs.json               # Tracked specifications
│   ├── uvicorn.pid              # Development server PID
│   ├── prompts/                 # Saved prompts and schemas
│   └── backups/                 # Implementation backups
├── specifications/
│   ├── users_v1.0.0.yaml        # Immutable versions
│   ├── users_v1.1.0.yaml
│   └── latest/                  # Symlink to the current version
│       └── users.yaml -> ../users_v1.1.0.yaml
├── implementations/             # Generated service classes
│   ├── users_service.py         # Database-ready CRUD implementations
│   └── products_service.py      # Customizable business logic
└── main.py                      # FastAPI application
```

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Setup and basic usage
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical architecture and component details  
- **[Database Setup](docs/DATABASE_SETUP.md)** - SQL backend configuration
- **[Changelog](CHANGELOG.md)** - Release notes and version history

## Development

### Testing
You can run the test suite using `make`:

```bash
# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Generate a coverage report
make coverage
```

### Formatting and Linting
This project uses `black` for formatting and `flake8` for linting.

```bash
# Format the code
make format

# Run the linter
make lint
```

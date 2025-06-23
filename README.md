# LiveAPI

**A Python framework for generating and serving REST APIs from OpenAPI specifications.**

LiveAPI combines interactive spec generation, immutable versioning, change detection, and a default resource service to provide instant, standardized APIs from OpenAPI specifications.

## Key Features

### 🤖 Interactive Spec Generation
- **Interactive Generation**: Interactively generate OpenAPI specifications from high-level prompts.
- **Schema-First Workflow**: Start with a simple JSON schema for your objects; LiveAPI infers the rest.
- **Editable Intermediates**: Edit the generated JSON schema directly for fine-grained control.
- **Smart Regeneration**: Automatically rebuilds specs from edited schemas.
- **Standards Compliant**: Generates OpenAPI 3.0 specs with professional error handling (RFC 7807).

### 🚀 Database-Ready Implementation Generation
- **Customizable Service Classes**: Generates implementation files with CRUD method overrides for database integration.
- **Database Integration Points**: Clear hooks for connecting PostgreSQL, MongoDB, or any database.
- **Business Logic Hooks**: Built-in spots for validation, logging, caching, and event publishing.
- **Dynamic Resource Service Fallback**: Uses LiveAPI's dynamic resource service as a foundation while allowing full customization.
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

LiveAPI simplifies API creation from spec to running server.

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
liveapi regenerate .liveapi/prompts/users_prompt.json

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

### 1. Installation
```bash
git clone <repository-url>
cd liveapi
pip install -e .
```

### 2. Initialization
```bash
mkdir my-api-project
cd my-api-project
liveapi init
```

### 3. Generate API Specification
```bash
liveapi generate
```
Follow the interactive prompts to define your API resource.

### 4. Sync
```bash
liveapi sync
# ✅ Created: implementations/users_service.py (customizable database service)
# ✅ Created: main.py (FastAPI app using your service)
# 🎯 Customize implementations/users_service.py for real data stores
```

### 5. Run Your API
```bash
# Start development server with auto-reload
liveapi run

# Start in background
liveapi run --background

# Check server health
liveapi ping

# Stop server
liveapi kill

# Access your API:
# http://localhost:8000/docs    # Interactive API docs
# http://localhost:8000/health  # Health check endpoint
```

## CRUD+ Interface

LiveAPI automatically provides standardized CRUD+ operations for any resource.

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

### Custom Service Class (Database-Ready)
```python
# implementations/users_service.py (auto-generated)
"""UserService - Database-connected implementation for users API."""

from liveapi.implementation import create_app
from liveapi.implementation.default_resource_service import DefaultResourceService
from typing import Dict, List, Any, Optional
import uuid

class UserService(DefaultResourceService):
    """Custom users service with database integration."""
    
    def __init__(self):
        # TODO: Initialize your database connection
        # self.db = PostgreSQLConnection()
        # self.logger = YourLogger()
        self._storage: Dict[str, Dict[str, Any]] = {}
    
    async def create_user(self, user_data: dict) -> dict:
        """Create a new user in your database."""
        from fastapi import HTTPException
        from liveapi.implementation.exceptions import ValidationError, ConflictError
        
        try:
            # Business validation
            if not user_data.get("email"):
                raise ValidationError(
                    message="Email is required",
                    details={"field": "email", "error": "missing_required_field"}
                )
            
            # TODO: Replace with your database insert
            # result = await self.db.insert_one("users", {
            #     "id": str(uuid.uuid4()),
            #     **user_data,
            #     "created_at": datetime.utcnow()
            # })
            
            # In-memory implementation (replace with database)
            user_id = str(uuid.uuid4())
            user_record = {"id": user_id, **user_data}
            self._storage[user_id] = user_record
            
            # TODO: Add business logic here
            # - Logging, caching, event publishing
            
            return user_record
            
        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Other CRUD methods: get_user, list_users, update_user, delete_user...

# Create the FastAPI app
def create_custom_app():
    """Create FastAPI app with database-connected users service."""
    app = create_app("specifications/users.yaml", custom_handlers={"users": UserService()})
    return app
```

### Main Application
```python
# main.py (auto-generated)
"""FastAPI application using custom LiveAPI implementations."""

import importlib.util
from pathlib import Path
from fastapi import FastAPI

# Auto-discover and load custom service implementations
app = FastAPI(title="Custom LiveAPI Services")

def discover_and_mount_services():
    """Discover service files and mount their apps."""
    implementations_dir = Path(__file__).parent / "implementations"
    service_files = list(implementations_dir.glob("*_service.py"))
    
    for service_file in service_files:
        # Import the service module
        spec = importlib.util.spec_from_file_location(service_file.stem, service_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Mount the custom app
        if hasattr(module, 'create_custom_app'):
            custom_app = module.create_custom_app()
            resource_name = service_file.stem.replace('_service', '')
            app.mount(f"/{resource_name}s", custom_app)

discover_and_mount_services()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

## Command Reference

### Project Management
```bash
liveapi init                   # Initialize project
liveapi generate               # Generate OpenAPI spec interactively
liveapi regenerate <prompt>    # Regenerate from a saved prompt
liveapi status                 # Show changes and sync status
liveapi validate               # Validate OpenAPI specs
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

## Development

### Testing
You can run the test suite using `make`:

```bash
# Run all tests
make test

f# Generate a coverage report
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

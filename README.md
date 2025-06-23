# LiveAPI

**A Python framework for generating and serving REST APIs from OpenAPI specifications.**

LiveAPI combines interactive spec generation, immutable versioning, change detection, and dynamic CRUD+ handlers to provide instant, standardized APIs from OpenAPI specifications.

## Key Features

### 🤖 Interactive Spec Generation
- **Interactive Generation**: Interactively generate OpenAPI specifications from high-level prompts.
- **Schema-First Workflow**: Start with a simple JSON schema for your objects; LiveAPI infers the rest.
- **Editable Intermediates**: Edit the generated JSON schema directly for fine-grained control.
- **Smart Regeneration**: Automatically rebuilds specs from edited schemas.
- **Standards Compliant**: Generates OpenAPI 3.0 specs with professional error handling (RFC 7807).

### 🚀 Dynamic CRUD+ Runtime
- **Zero Code Generation**: APIs are served dynamically from OpenAPI specs without generating handler code.
- **Dynamic Pydantic Models**: Runtime model generation from OpenAPI schemas ensures type safety.
- **Built-in Features**: Filtering, validation, and professional error handling out of the box.
- **Correct by Default**: Handles parameters, schemas, and responses according to best practices.
- **Instant Deployment**: No compilation or build steps required.

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

# 4. Sync to create the main application file
liveapi sync
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
# ✅ Created: main.py
# 🎯 Run 'liveapi run' or 'python main.py' to start your API server
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

## Generated `main.py` Example

### Single API
```python
# main.py (auto-generated)
"""FastAPI application using LiveAPI CRUD+ handlers."""

import uvicorn
from liveapi.implementation import create_app

# Create the app from OpenAPI specification
app = create_app("specifications/users_v1.0.0.yaml")

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

### Multiple APIs
```python
# main.py (auto-generated for multiple specs)
"""FastAPI application combining multiple APIs using LiveAPI CRUD+ handlers."""

import uvicorn
from fastapi import FastAPI
from liveapi.implementation import create_app as create_app_1
from liveapi.implementation import create_app as create_app_2

# Create individual apps
app_1 = create_app_1("specifications/users_v1.0.0.yaml")
app_2 = create_app_2("specifications/products_v1.0.0.yaml")

# Main app that combines all APIs
app = FastAPI(
    title="Combined LiveAPI Services",
    description="Multiple CRUD+ APIs combined into one service"
)

# Mount each API under its own prefix
app.mount("/users", app_1)
app.mount("/products", app_2)

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
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
liveapi sync                  # Synchronize main.py with specs
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
└── main.py                      # FastAPI application
```

## Development

### Testing
You can run the test suite using `make`:

```bash
# Run all tests
make test

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

# LiveAPI

**Opinionated CRUD+ API Engine with AI-Powered Specification Generation**

A Python framework that combines **AI-powered spec generation**, **immutable versioning**, **change detection**, and **dynamic CRUD+ handlers** to provide instant, standardized APIs from OpenAPI specifications.

## Key Features

### 🤖 AI-Powered Spec Generation (IMPROVED!)
- **Streamlined UX**: No duplicate questions, object-first workflow with smart auto-inference
- **Interactive prompts**: Start with resource name, API details auto-suggested
- **JSON array examples**: Clean format for providing multiple example objects
- **Dual persistence**: Saves both prompts AND intermediate JSON schema for editing
- **Schema editing**: Edit the clean JSON structure instead of complex OpenAPI YAML
- **Smart regeneration**: Detects schema edits and rebuilds specs automatically
- **Standards compliance**: RFC 7807 errors, proper FastAPI implementation, <200ms SLA
- **Ready-to-use specs**: Generate complete OpenAPI 3.0 specifications instantly

### 🚀 CRUD+ Runtime Engine (IMPROVED!)
- **Zero code generation**: APIs served dynamically from OpenAPI specs
- **Correct parameter handling**: Uses 'id' instead of 'resource_id' in endpoints
- **Proper schema handling**: Typed Pydantic models instead of generic objects
- **Array responses**: List endpoints return proper array types, not strings
- **RFC 7807 validation errors**: Professional error format with correct Content-Type
- **Dynamic Pydantic models**: Runtime model generation from OpenAPI schemas
- **Built-in features**: Filtering, validation, professional error handling
- **Instant deployment**: No compilation or build steps required

### 🔄 API Lifecycle Management
- **Immutable versioning**: Specs become read-only versions (`users.yaml` → `users_v1.0.0.yaml`)
- **Change detection**: SHA256-based tracking with breaking vs non-breaking analysis
- **Implementation sync**: Keep main.py synchronized with spec changes
- **Migration planning**: Automated guides with effort estimation

### 🛡️ Safe Evolution
- **Preview mode**: See changes before applying them
- **Automatic backups**: Rollback capability for all changes
- **Team collaboration**: Shared `.liveapi/` metadata
- **Git integration**: Version control ready

### 📊 Complete Visibility
- **Change analysis**: Detailed breaking change detection
- **Version comparison**: Diff any two versions
- **Sync status**: Track what's changed and what needs updating
- **Migration effort**: Time estimates for updates

## How It Works

LiveAPI combines structured spec generation with a runtime CRUD+ engine (no auth complexity):

```bash
# 1. Interactive start (IMPROVED!)
liveapi
# 🚀 Welcome to LiveAPI CRUD Generator!
# Choose: Initialize + generate spec, or use existing specs

# 2. Generate specs with streamlined workflow
liveapi generate
# Object name: > users
# Object description: > User account records
# API name (auto-suggested: Users API): > 
# API description (auto-suggested: User account records): >
# JSON schema: {"name": "string", "email": "string", "active": "boolean"}
# JSON array examples: [{"name": "Alice", "email": "alice@example.com", "active": true}]
# 💾 Prompt saved to: .liveapi/prompts/users_prompt.json
# 📋 Schema saved to: .liveapi/prompts/users_schema.json

# 2b. Edit the clean JSON schema (easier than OpenAPI YAML!)
vim .liveapi/prompts/users_schema.json
liveapi regenerate .liveapi/prompts/users_prompt.json
# 🔧 Schema has been modified - using edited schema

# 3. Check status
liveapi status
# ✅ Users API: ready for sync

# 4. Sync creates simple main.py (no code generation!)
liveapi sync
# 🚀 LiveAPI CRUD+ Mode - No code generation needed!
# ✅ Created: main.py

# 5. Run your API immediately
liveapi run
# 🎯 Dynamic CRUD+ handlers with proper schemas and RFC 7807 errors
# Test with: curl http://localhost:8000/users
# DELETE: curl -X DELETE http://localhost:8000/users/1  (uses 'id', not 'user_id')

# 6. Built-in server management
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

### 2. Quick Start - Interactive Mode
```bash
cd my-api-project
liveapi

# 🚀 Welcome to LiveAPI!
# This will guide you through initialization and optional spec generation
```

### 3. Alternative - Manual Initialization
```bash
cd my-api-project
liveapi init

# Creates:
# .liveapi/
# ├── config.json    # Project configuration
# └── specs.json     # Specification tracking
```

### 4. Generate API Specifications

#### Option A: AI Generation (Improved UX)
```bash
liveapi generate

# Streamlined interactive prompts:
# Object name: > users
# Object description: > User account records  
# API name (auto-suggested: Users API): > 
# API description (auto-suggested: User account records): >
# JSON schema: {"name": "string", "email": "string", "active": "boolean"}
# JSON array examples: [
#   {"name": "Alice", "email": "alice@example.com", "active": true},
#   {"name": "Bob", "email": "bob@example.com", "active": false}
# ]
```

#### Option B: Manual OpenAPI Specs
```yaml
# users.yaml
openapi: 3.0.0
info:
  title: Users API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: list_users
      responses:
        '200':
          description: List of users
  /users/{id}:
    get:
      operationId: get_user
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User details
```

### 5. Sync (Creates Simple main.py)
```bash
liveapi sync

# 🚀 LiveAPI CRUD+ Mode - No code generation needed!
# ✅ Created: main.py
# 🎯 Run 'liveapi run' or 'python main.py' to start your API server
```

### 6. Run Your API
```bash
# Start development server
liveapi run                    # Foreground mode with auto-reload
liveapi run --background       # Background mode with PID management

# Check server health
liveapi ping                   # Health check with response time

# Stop server
liveapi kill                   # Graceful shutdown

# Access your API:
# http://localhost:8000/docs    # Interactive API docs  
# http://localhost:8000/health  # Health check endpoint
```

## CRUD+ Interface

LiveAPI automatically provides standardized CRUD+ operations for any resource:

```bash
# Create (with proper typed schemas)
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "active": true}'

# Read (using 'id' parameter)
curl http://localhost:8000/users/123

# Update (with proper typed schemas)
curl -X PUT http://localhost:8000/users/123 \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "email": "alice@example.com", "active": true}'

# Delete (using 'id' parameter, not 'user_id')
curl -X DELETE http://localhost:8000/users/123

# List (returns proper array, not string)
curl "http://localhost:8000/users?limit=10&offset=0"

# Invalid data gets RFC 7807 error response with proper Content-Type
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
# Returns: {"errors": [{"title": "Unprocessable Entity", "detail": "...", "status": "422"}]}
```

## Generated Main.py Example

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

## Workflow Examples

### Starting from Scratch (NEW!)
```bash
# Interactive mode - fastest way to get started
liveapi

# 🚀 Welcome to LiveAPI!
# 1. Initialize a new project and generate an API spec
# 2. Initialize with existing OpenAPI specs
# 3. Show help
# Enter your choice (1-3): 1

# Project name: User Management
# API name: User Management API
# Description: User accounts and profile management
# Endpoints: /users with CRUD operations...
# ✅ Generated: user_management_api.yaml
# ✅ Project initialized
# 🎯 Next: Run 'liveapi sync' to prepare runtime
```

### Making API Changes
```bash
# 1. Edit your OpenAPI spec or regenerate
vim users.yaml  # Add new endpoint
# OR
liveapi regenerate .liveapi/prompts/users_prompt.json

# 2. Check what changed
liveapi status
# 📝 users.yaml has non-breaking changes
#    Added: POST /users/search

# 3. Create new version
liveapi version create --minor
# ✅ Created users_v1.1.0.yaml

# 4. Update main.py
liveapi sync
# ✅ Updated: main.py
# 🎯 Your API now includes the new endpoints dynamically!
```

### Breaking Changes
```bash
# 1. Make breaking change
vim users.yaml  # Remove required field

# 2. Check impact
liveapi status
# ⚠️ users.yaml has BREAKING changes
#    Removed required field: email

# 3. Create major version
liveapi version create --major
# ✅ Created users_v2.0.0.yaml

# 4. Sync with migration awareness
liveapi sync
# ✅ Updated: main.py
# ⚠️ Breaking changes detected - review API documentation
```

## Command Reference

### Project Management
```bash
liveapi                        # Interactive mode (NEW!)
liveapi init                   # Initialize project
liveapi generate               # Generate OpenAPI spec with AI
liveapi regenerate <prompt>    # Regenerate from saved prompt (NEW!)
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
liveapi version create         # Auto-detect version type
liveapi version create --major # Breaking changes
liveapi version create --minor # New features
liveapi version create --patch # Bug fixes
liveapi version list          # List all versions
liveapi version compare v1 v2 # Compare versions
```

### Synchronization
```bash
liveapi sync                  # Synchronize main.py
liveapi sync --preview        # Preview changes only
liveapi sync --force         # Skip confirmations
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
│   ├── users_v1.0.0.yaml       # Immutable versions
│   ├── users_v1.1.0.yaml
│   └── latest/                  # Current versions
│       └── users.yaml -> ../users_v1.1.0.yaml
└── main.py                      # Simple FastAPI application
```


## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run liveapi-specific tests
python -m pytest tests/test_liveapi*.py -v
```

## Features

✅ **Implemented**:
- **Streamlined UX** - no duplicate questions, object-first workflow with smart defaults
- **Professional FastAPI implementation** - correct parameter names, typed schemas, RFC 7807 errors
- **JSON array examples** - clean format for providing multiple example objects
- **CRUD+ Runtime Engine** with dynamic handlers (NEW!)
- **Zero code generation** - APIs served from specs directly (NEW!)
- **AI-powered spec generation** with improved interactive workflow
- **Interactive mode** for guided project setup
- **Development server management** with PID tracking and health checks
- **Standards compliance** (RFC 7807 errors, proper Content-Type, <200ms SLA)
- **Schema editing workflow** for easy API modifications
- Immutable versioning with semantic versioning
- SHA256-based change detection
- Breaking vs non-breaking change classification
- Implementation synchronization (now creates simple main.py)
- Migration guide generation
- Backup and recovery system
- Preview mode for all operations
- Multi-API project support
- Team collaboration via shared metadata
- 67 comprehensive tests (including UX improvements)

🚧 **Roadmap**:
- Database integration plugins
- Authentication middleware
- Custom business logic hooks
- Performance optimization
- Cloud deployment guides

## License

[Your License]

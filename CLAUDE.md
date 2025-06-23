# CLAUDE.md

This file provides guidance when working with code in this repository.

## Project Overview

This is **LiveAPI** - a comprehensive API lifecycle management system that handles OpenAPI specification evolution, version control, change detection, and implementation synchronization. LiveAPI ensures safe API evolution with immutable versioning, automated change detection, and intelligent migration planning.

**Current Status**: Production-ready with complete lifecycle management features implemented and tested.

## Architecture

LiveAPI follows this modular package structure:
```
liveapi/
├── src/
│   └── liveapi/
│       ├── __init__.py
│       ├── metadata_manager.py    # Facade for metadata package
│       ├── metadata/              # Metadata management package
│       │   ├── __init__.py        # Re-exports
│       │   ├── manager.py         # Main MetadataManager class
│       │   ├── models.py          # Data models
│       │   └── utils.py           # Helper functions
│       ├── change_detector.py     # Facade for change_detector package
│       ├── change_detector/       # Change detection package
│       │   ├── __init__.py        # Re-exports
│       │   ├── models.py          # Data models
│       │   ├── detector.py        # Main detector class
│       │   ├── analyzer.py        # Analysis logic
│       │   └── utils.py           # Helper functions
│       ├── version_manager.py     # Facade for version package
│       ├── version/               # Version management package
│       │   ├── __init__.py        # Re-exports
│       │   ├── manager.py         # Main VersionManager class
│       │   ├── models.py          # Version models
│       │   ├── comparator.py      # Version comparison
│       │   └── migration.py       # Migration planning
│       ├── sync_manager.py        # Facade for sync package
│       ├── sync/                  # Synchronization package
│       │   ├── __init__.py        # Re-exports
│       │   ├── manager.py         # Main SyncManager class
│       │   ├── plan.py            # Sync planning
│       │   ├── executor.py        # Sync execution
│       │   ├── models.py          # Sync models
│       │   └── migration.py       # Migration guides
│       ├── spec_generator.py      # Facade for generator package
│       ├── generator/             # Specification generation package
│       │   ├── __init__.py        # Re-exports
│       │   ├── generator.py       # Main SpecGenerator class
│       │   ├── prompt.py          # Prompt building
│       │   ├── interactive.py     # Interactive workflow
│       │   └── utils.py           # Helper functions
│       ├── cli.py                 # Facade for CLI package
│       ├── cli/                   # CLI package
│       │   ├── __init__.py        # Re-exports
│       │   ├── main.py            # Main entry point
│       │   ├── utils.py           # CLI utilities
│       │   └── commands/          # Command implementations
│       │       ├── __init__.py
│       │       ├── project.py
│       │       ├── version.py
│       │       ├── sync.py
│       │       ├── generate.py
│       │       └── server.py
│       └── implementation/        # Implementation generation (formerly automatic)
│           ├── __init__.py        # Re-exports
│           ├── app.py             # FastAPI app creation
│           ├── parser.py          # OpenAPI parsing
│           ├── router.py          # Route generation
│           ├── scaffold.py        # Code scaffolding
│           └── templates/         # Code templates
├── .liveapi/                      # Project metadata
│   ├── config.json               # Project configuration
│   ├── specs.json                # Specification tracking
│   └── backups/                  # Implementation backups
├── specifications/               # Versioned OpenAPI specs
├── implementations/              # Generated FastAPI code
├── tests/
└── pyproject.toml
```

### Core Components
- **MetadataManager** (`metadata/` package): Manages project state and spec tracking with checksums
- **ChangeDetector** (`change_detector/` package): Detects and analyzes breaking vs non-breaking changes  
- **VersionManager** (`version/` package): Handles immutable semantic versioning
- **SyncManager** (`sync/` package): Synchronizes implementations with specification changes
- **SpecGenerator** (`generator/` package): Generates OpenAPI specifications using structured templates
- **CLI Interface** (`cli/` package): Provides command-line interface for all LiveAPI operations
- **Implementation** (`implementation/` package): Handles implementation generation from OpenAPI specs

## Refactoring Plan

We've started refactoring large files into modular packages to improve maintainability. The pattern is:

1. Create a package directory with the same name as the original file
2. Split the code into logical modules:
   - `__init__.py` - Re-exports public components
   - `models.py` - Data models and classes
   - Core functionality in appropriately named modules
   - `utils.py` - Helper functions
3. Convert the original file to a facade that imports from the new structure

### Completed Refactorings:
- ✅ `cli.py` → `cli/` package
- ✅ `change_detector.py` → `change_detector/` package
- ✅ `version_manager.py` → `version/` package
- ✅ `sync_manager.py` → `sync/` package
- ✅ `spec_generator.py` → `generator/` package
- ✅ `metadata_manager.py` → `metadata/` package

All planned refactorings have been completed! The codebase now follows a modular package structure for improved maintainability.

## Core Workflow

LiveAPI manages the complete API lifecycle through these key phases:

### 0. Interactive Spec Generation (IMPROVED!)
```bash
# Run with no arguments for interactive mode
liveapi

# Or use the generate command directly
liveapi generate

# Regenerate from saved prompt (NEW!)
liveapi regenerate .liveapi/prompts/my_api_prompt.json
```
- **Streamlined UX** - no duplicate questions, smart auto-inference
- **Object-first workflow** - start with your resource, API details follow
- **Smart defaults** - API name/description auto-inferred from resource info
- **JSON array examples** - provide multiple examples in clean JSON format
- **Professional error handling** - RFC 7807 compliant validation errors
- **Saves schemas for regeneration** - easily iterate on API designs
- **Schema editing workflow** - edit clean JSON instead of complex OpenAPI YAML

### 1. Project Initialization
```bash
liveapi init
```
- Creates `.liveapi/` metadata directory
- Discovers existing OpenAPI specifications
- Tracks initial checksums for change detection

### 2. Change Detection
```bash
liveapi status
```
- Compares current specs against tracked checksums
- Classifies changes as breaking vs non-breaking
- Provides impact analysis and version recommendations

### 3. Version Management
```bash
# Create version automatically based on changes
liveapi version create

# Create specific version types
liveapi version create --major    # Breaking changes
liveapi version create --minor    # New features
liveapi version create --patch    # Bug fixes

# List all versions
liveapi version list

# Compare versions
liveapi version compare v1.0.0 v1.1.0
```
- Creates immutable version files (e.g., `users_v1.0.0.yaml`)
- Updates symlinks to latest versions
- Preserves full version history

### 4. Implementation Synchronization
```bash
# Preview sync changes
liveapi sync --preview

# Execute synchronization
liveapi sync

# Force sync (skip confirmations)
liveapi sync --force
```
- Automatically generates FastAPI implementations
- Creates backups before making changes
- Generates migration guides for breaking changes
- Handles implementation updates safely

## Key Features

### Immutable Versioning
- Never overwrites existing specifications
- Semantic versioning (major.minor.patch)
- Symlinks to latest versions for easy access
- Complete version history preservation

### Smart Change Detection
- SHA256 checksums for fast change identification
- Breaking vs non-breaking change classification
- Detailed analysis of paths, schemas, parameters, and responses
- Automatic version impact assessment

### Safe Migration Planning
- Backup creation before any changes
- Migration guides for breaking changes
- Effort estimation (low/medium/high)
- Preview mode for safe operations

### Team Collaboration
- Shared metadata via `.liveapi/` directory
- Git-compatible version control integration
- Clear change visibility and impact analysis
- Synchronized project state across team members

### CRUD+ Implementation Generation
- **Opinionated CRUD+ mode** for standardized APIs
- Automatic detection of CRUD+ resources in OpenAPI specs
- Dynamic Pydantic model generation using create_model
- Standard handlers for Create, Read, Update, Delete, List operations
- **Correct parameter naming** - uses 'id' instead of 'resource_id'
- **Proper request/response schemas** - typed models instead of generic objects
- **Array responses** - list endpoints return proper array types
- **RFC 7807 validation errors** - professional error format with proper Content-Type
- Simple list responses (no pagination complexity)
- In-memory storage (easily replaceable with database)
- **No authentication** - handled at API Gateway level

## Command Reference

### Project Management
```bash
liveapi                        # Interactive mode (new!)
liveapi init                   # Initialize project
liveapi generate               # Generate OpenAPI spec with AI
liveapi regenerate <prompt>    # Regenerate from saved prompt (NEW!)
liveapi status                 # Show changes and sync status
liveapi validate               # Validate OpenAPI specs
```

### Version Control
```bash
liveapi version create         # Auto-version based on changes
liveapi version create --major # Create major version
liveapi version create --minor # Create minor version
liveapi version create --patch # Create patch version
liveapi version list          # List all versions
liveapi version compare v1 v2 # Compare versions
```

### Synchronization
```bash
liveapi sync                  # Sync implementations
liveapi sync --preview        # Preview changes only
liveapi sync --force         # Skip confirmations
```

## Installation and Usage

1. Install liveapi:
```bash
pip install -e .
```

2. No setup required - just run the generator:
```bash
liveapi generate
```

3. Initialize your project:
```bash
# Navigate to your project directory
cd my-api-project

# Interactive mode - will offer to generate a spec
liveapi

# Or initialize directly
liveapi init
```

4. Typical workflow (improved UX):
```bash
# Generate a new API spec with streamlined workflow
liveapi generate
# Interactive prompts:
# 1. Object name (e.g., "products") 
# 2. Object description (e.g., "Product inventory items")
# 3. API name (auto-suggested: "Products API")
# 4. API description (auto-suggested from object description)
# 5. JSON schema for fields
# 6. JSON array of examples
# 
# 🎯 Next steps:
#   1. Review the generated spec: specifications/products.yaml
#   2. Edit the schema JSON for quick changes: .liveapi/prompts/products_schema.json
#   3. Run 'liveapi sync' to generate implementation
#   4. Run 'liveapi run' to test the API
#   5. Test with proper schemas: curl http://localhost:8000/products
#   6. Run 'liveapi version create' when ready to version

# Edit your OpenAPI specs or regenerate with modifications
liveapi regenerate .liveapi/prompts/products_prompt.json

# Sync implementations and test (with improved FastAPI)
liveapi sync           # Generate FastAPI code with correct parameters
liveapi run            # Start development server
# Test with properly typed responses and RFC 7807 error handling

# Version when ready
liveapi version create --minor
```

## Workflow Examples

### Starting a New Project
```bash
# Option 1: Interactive mode (recommended)
liveapi
# Follow prompts to initialize and generate your first spec

# Option 2: Manual approach
liveapi init
liveapi generate  # Generate spec with AI
liveapi status    # Check status
liveapi sync      # Generate implementations
```

### Evolving an Existing API
```bash
# 1. Edit your OpenAPI specification
# Or regenerate with modifications:
liveapi regenerate .liveapi/prompts/my_api_prompt.json

# 2. Check what changed
liveapi status

# 3. Create version if breaking changes
liveapi version create --major

# 4. Sync implementations
liveapi sync --preview
liveapi sync
```

### Working with Multiple APIs
```bash
# LiveAPI handles multiple specs automatically
ls specifications/
# users_v1.0.0.yaml
# products_v1.1.0.yaml  
# orders_v2.0.0.yaml

# Status shows all APIs
liveapi status

# Sync handles all at once
liveapi sync
```

### Iterating on API Design with Saved Prompts & Schema Editing
```bash
# Generate initial spec (automatically saves prompt AND intermediate JSON)
liveapi generate
# 💾 Prompt saved to: .liveapi/prompts/my_api_prompt.json
# 📋 Schema saved to: .liveapi/prompts/my_api_schema.json
#    Edit the schema JSON to modify endpoints/objects, then:
#    liveapi regenerate .liveapi/prompts/my_api_prompt.json

# Method 1: Edit the intermediate JSON schema (EASIER!)
vim .liveapi/prompts/my_api_schema.json
# Edit endpoints, add/remove objects, modify fields
liveapi regenerate .liveapi/prompts/my_api_prompt.json
# 🔧 Schema has been modified - using edited schema

# Method 2: Edit the original prompt and regenerate
liveapi regenerate .liveapi/prompts/my_api_prompt.json
# Choose to edit prompt, then regenerates with LLM

# List available saved prompts and schemas
ls .liveapi/prompts/
# my_api_prompt.json       <- Original prompt
# my_api_schema.json       <- Intermediate JSON (easy to edit!)
# user_service_prompt.json
# user_service_schema.json

# The regenerate workflow gives you TWO ways to iterate:
# 1. Edit the structured JSON schema (recommended for precise changes)
# 2. Edit the original prompt (good for major redesigns)
# 3. Use the exact same prompt to get different LLM output
# 4. Change models (--model flag)
```

### Creating CRUD APIs with Custom Schemas (Improved)
```bash
# Generate a CRUD API with streamlined workflow
liveapi generate
# New improved prompts:
# 1. Object name: "locations"
# 2. Description: "Gallery location records"  
# 3. API name: (auto-suggested: "Locations API")
# 4. API description: (auto-suggested: "Gallery location records")
# 5. JSON schema:
#    {
#      "site": "string",
#      "room": "string", 
#      "active": "integer",
#      "description": "string",
#      "unitPosition": "string"
#    }
# 6. JSON array examples:
#    [
#      {"site": "Main Gallery", "room": "101", "active": 1, "description": "Main entrance", "unitPosition": "A1"},
#      {"site": "Annex", "room": "202", "active": 1, "description": "Storage area", "unitPosition": "B2"}
#    ]

# Sync to generate implementation (with proper FastAPI)
liveapi sync

# Run the API (with RFC 7807 errors and correct parameters)
liveapi run
# Test: curl http://localhost:8000/locations
# DELETE: curl -X DELETE http://localhost:8000/locations/1  (uses 'id', not 'locationID')
```

## Testing

Run tests with:
```bash
python -m pytest tests/ -v
```

## Status

✅ **LiveAPI Features Implemented**:
- **Streamlined UX workflow** - no duplicate questions, object-first approach
- **Smart auto-inference** - API name/description inferred from resource info  
- **JSON array examples** - clean format for providing multiple examples
- **Professional FastAPI implementation** - correct parameter names ('id' not 'resource_id')
- **RFC 7807 validation errors** - proper Content-Type and error structure
- **Typed request/response schemas** - real Pydantic models, not generic objects
- **Proper array responses** - list endpoints return correct array types
- **Dual persistence system** - saves prompts AND intermediate JSON schemas
- **Schema editing workflow** - edit clean JSON instead of complex OpenAPI YAML
- **Smart regeneration** - detects schema modifications and rebuilds automatically
- **Interactive mode** when running `liveapi` with no arguments
- **Immutable versioning system** with semantic versioning support
- **Change detection** with breaking/non-breaking analysis using SHA256 checksums
- **Implementation synchronization** with automatic FastAPI code generation  
- **Migration planning** with effort estimation and manual intervention detection
- **Version comparison** with detailed change breakdowns
- **Backup and recovery** for safe implementation updates
- **Preview mode** for all destructive operations
- **Complete CLI interface** with all essential commands
- **67 comprehensive tests** covering all functionality with 100% pass rate
- **Team collaboration** via shared `.liveapi/` metadata
- **Git integration** ready for version control workflows
- **CRUD+ implementation generation** with automatic resource detection
- **Dynamic Pydantic model generation** for robust type validation
- **Simplified CRUD-only architecture** with streamlined handlers
- **Cloud-friendly testing** that works reliably in all development environments

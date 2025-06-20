# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "automatic" - a Python framework that dynamically creates FastAPI routes from OpenAPI specifications at runtime, eliminating code generation. The core concept is to parse OpenAPI specs and generate FastAPI routes dynamically, allowing business logic to be implemented as pure functions with dict-based interfaces.

## Architecture

The project follows this planned structure:
```
automatic/
├── src/
│   └── automatic/
│       ├── __init__.py
│       ├── parser.py     # OpenAPI parsing logic
│       ├── router.py     # Dynamic route generation
│       └── app.py        # Main application interface
├── tests/
├── examples/
└── pyproject.toml
```

### Core Components
- **Parser**: Loads and parses OpenAPI YAML/JSON specifications
- **Router**: Generates FastAPI routes dynamically from parsed specs
- **App Interface**: Main entry point (`automatic.create_app()`) that ties everything together

### Business Logic Interface
Implementation classes should provide methods that match OpenAPI `operationId` values:
```python
class MyImplementation:
    def create_art_object(self, data: dict) -> tuple[dict, int]:
        # Returns (response_data, status_code)
        return {"id": 1, "title": data["title"]}, 201
```

## Development Setup

This project uses Poetry for dependency management with these core dependencies:
- FastAPI ^0.100.0
- Pydantic ^2.0.0
- PyYAML ^6.0
- Python ^3.9
- Prance ^25.0.0 (for OpenAPI parsing)

## Installation and Usage

1. Install in development mode:
```bash
pip install -e .
```

2. Use the framework:
```python
import automatic
app = automatic.create_app("api.yaml", MyImplementation())
```

## Testing

Run tests with:
```bash
python -m pytest tests/ -v
```

## Example

A complete working example is available in `examples/`:
- `examples/api.yaml` - OpenAPI specification
- `examples/my_api.py` - Implementation class
- `examples/run_example.py` - Runnable server

## Status

✅ **MVP Complete** - All core features implemented:
- OpenAPI spec parsing with prance
- Dynamic FastAPI route generation
- Dict-based business logic interface
- Request validation and routing
- Working example with CRUD operations
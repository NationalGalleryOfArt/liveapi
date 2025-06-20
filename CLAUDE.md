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

**Basic Pattern**:
```python
class MyImplementation:
    def create_art_object(self, data: dict) -> tuple[dict, int]:
        # Returns (response_data, status_code)
        return {"id": 1, "title": data["title"]}, 201
```

**Exception-Based Pattern** (recommended):
```python
from automatic import NotFoundError, ValidationError, ConflictError

class MyImplementation:
    def get_art_object(self, data: dict):
        # Auth info is available in data['auth'] if authentication is configured
        auth_info = data.get('auth')
        
        art_id = data["art_id"]
        if art_id not in self.objects:
            raise NotFoundError(f"Art object {art_id} not found")
        return self.objects[art_id], 200
    
    def create_art_object(self, data: dict):
        # Check authentication if required
        auth_info = data.get('auth')
        if not auth_info:
            raise UnauthorizedError("Authentication required")
            
        if not data.get("title"):
            raise ValidationError("Title is required")
        if self.title_exists(data["title"]):
            raise ConflictError("Art object with this title already exists")
        # Create and return object
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

**Automatic discovery** (default):
```python
import automatic
# Automatically finds api/ and implementations/ directories
app = automatic.create_app()
```

**Explicit specification**:
```python
from automatic import create_app

# Basic usage
app = create_app(spec_path="api.yaml", implementation=MyImplementation())

# With authentication
from automatic import create_api_key_auth, create_bearer_auth

# API Key authentication
auth = create_api_key_auth(api_keys=['secret-key-123', 'secret-key-456'])
app = create_app(spec_path="api.yaml", implementation=MyImplementation(), auth_dependency=auth)

# Bearer token authentication
auth = create_bearer_auth(tokens=['token-123', 'token-456'])
app = create_app(spec_path="api.yaml", implementation=MyImplementation(), auth_dependency=auth)
```

## Testing

Run tests with:
```bash
python -m pytest tests/ -v
```

## Authentication

Automatic provides built-in authentication support for securing API endpoints:

### API Key Authentication

Header-based API key authentication using `X-API-Key` header:

```python
from automatic import create_api_key_auth

# Multiple configuration options:

# 1. List of valid API keys
auth = create_api_key_auth(api_keys=['key1', 'key2', 'key3'])

# 2. Single API key
auth = create_api_key_auth(api_keys='single-secret-key')

# 3. Dictionary with metadata
auth = create_api_key_auth(api_keys={
    'admin-key': {'role': 'admin', 'permissions': ['read', 'write', 'delete']},
    'readonly-key': {'role': 'readonly', 'permissions': ['read']}
})

# 4. From environment variable (default: API_KEY)
auth = create_api_key_auth()  # Uses os.getenv('API_KEY')

# Apply to app
app = create_app(spec_path="api.yaml", implementation=MyImpl(), auth_dependency=auth)
```

**Usage**: `curl -H "X-API-Key: your-key" http://localhost:8000/endpoint`

### Bearer Token Authentication

Standard Authorization header with Bearer tokens:

```python
from automatic import create_bearer_auth

# Multiple configuration options:

# 1. List of valid tokens
auth = create_bearer_auth(tokens=['token1', 'token2', 'token3'])

# 2. Single token
auth = create_bearer_auth(tokens='single-secret-token')

# 3. Dictionary with metadata
auth = create_bearer_auth(tokens={
    'admin-token': {'user': 'admin', 'scope': 'full'},
    'api-token': {'user': 'service', 'scope': 'api'}
})

# 4. From environment variable (default: BEARER_TOKEN)
auth = create_bearer_auth()  # Uses os.getenv('BEARER_TOKEN')

# Apply to app
app = create_app(spec_path="api.yaml", implementation=MyImpl(), auth_dependency=auth)
```

**Usage**: `curl -H "Authorization: Bearer your-token" http://localhost:8000/endpoint`

### Authentication in Implementation Methods

When authentication is configured, auth information is passed to implementation methods:

```python
class MyImplementation:
    def get_protected_resource(self, data: dict):
        # Authentication info is available in data['auth']
        auth_info = data.get('auth')
        
        if not auth_info:
            raise UnauthorizedError("Authentication required")
        
        # Access auth metadata
        api_key = auth_info.get('api_key')  # For API key auth
        token = auth_info.get('token')      # For Bearer token auth
        metadata = auth_info.get('metadata')  # User-defined metadata
        
        # Your business logic here
        return {"message": "Access granted", "user": metadata}, 200
```

### Security Features

- ✅ **Header-only authentication** - No query parameters or cookies (security best practice)
- ✅ **RFC 9457 compliant error responses** - Standardized error format
- ✅ **Flexible token storage** - Lists, dicts, env vars, single values
- ✅ **Metadata support** - Associate additional data with keys/tokens
- ✅ **Global or per-route** - Apply to entire app or specific routes

## Exception Handling

Automatic provides built-in business exceptions that map to HTTP status codes:

```python
from automatic import (
    NotFoundError,        # 404
    ValidationError,      # 400
    ConflictError,        # 409
    UnauthorizedError,    # 401
    ForbiddenError,       # 403
    RateLimitError,       # 429
    ServiceUnavailableError  # 503
)
```

**Features**:
- Automatic RFC 9457 error responses
- Extra context data can be included
- Generic exceptions become safe 500 responses

**Example Response**:
```json
{
  "type": "/errors/not_found",
  "title": "NotFound",
  "status": 404,
  "detail": "User 123 not found",
  "user_id": "123"
}
```

## Examples

Working examples are available in `examples/`:
- `examples/convention-demo/` - Shows automatic multi-API discovery
- `examples/versioning/` - Demonstrates version-aware API handling
- `examples/exceptions/` - Exception handling patterns
- `examples/auth/` - Authentication examples (API key and Bearer token)

## Status

✅ **Production Ready** - All core features implemented:
- OpenAPI spec parsing with prance
- Dynamic FastAPI route generation
- Dict-based business logic interface
- Request validation with Pydantic models
- Path, query, and body parameter handling
- **Business exception mapping to HTTP responses**
- **Authentication (API Key & Bearer Token)**
- Automatic multi-API discovery
- Version-aware routing (v1, v2, etc.)
- RFC 9457 error responses
- Working examples demonstrating all features
- Comprehensive test coverage
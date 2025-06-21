# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is "automatic" - a Python framework that dynamically creates FastAPI routes from OpenAPI specifications at runtime, eliminating code generation. The core concept is to parse OpenAPI specs and generate FastAPI routes dynamically, while providing **Rails-style base classes** and **zero-configuration project setup** for maximum developer productivity.

**Current Status**: Work in progress with intelligent auto-discovery, CRUD base classes, authentication, and comprehensive testing.

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
├── specifications/      # OpenAPI specs directory
├── implementations/     # Business logic implementations
├── tests/
├── examples/
└── pyproject.toml
```

### Core Components
- **Parser**: Loads and parses OpenAPI YAML/JSON specifications
- **Router**: Generates FastAPI routes dynamically from parsed specs
- **App Interface**: Main entry point (`automatic.create_app()`) that ties everything together

### Business Logic Interface

Automatic provides **Rails-style base classes** to simplify implementation development. Choose the appropriate base class for your API pattern:

#### **CRUD APIs (Recommended for REST resources)**

For standard CRUD operations, inherit from `BaseCrudImplementation`:

```python
from automatic import BaseCrudImplementation

class UserService(BaseCrudImplementation):
    """CRUD implementation for user resources."""
    
    resource_name = "user"  # Used for error messages and resource identification
    
    def get_data_store(self) -> Dict[str, Any]:
        """Return your data storage mechanism."""
        # Replace with actual database/cache/service connection
        return self.database.get_collection("users")
    
    # Optional: Override CRUD methods for custom logic
    def validate_create(self, data: Dict) -> None:
        """Add custom validation for creating users."""
        super().validate_create(data)
        if len(data.get('name', '')) < 2:
            raise ValidationError("Name must be at least 2 characters")
    
    def build_resource(self, data: Dict, resource_id: str) -> Dict:
        """Customize how users are created."""
        return {
            "id": resource_id,
            "name": data.get('name'),
            "email": data.get('email'),
            "status": "active",
            "created_at": "2023-01-01T00:00:00Z",
            **data
        }
```

**Built-in CRUD Operations**:
- `index(filters, auth_info)` - List resources (GET /users)
- `show(resource_id, auth_info)` - Get single resource (GET /users/{id})
- `create(data, auth_info)` - Create resource (POST /users)
- `update(resource_id, data, auth_info)` - Update resource (PUT/PATCH /users/{id})
- `destroy(resource_id, auth_info)` - Delete resource (DELETE /users/{id})

**Automatic Method Mapping**: Your OpenAPI operation methods automatically delegate to CRUD operations:

```python
def get_user(self, data: dict):
    # Automatically extracts user_id and delegates to self.show()
    resource_id = data.get('user_id')
    return self.show(resource_id, auth_info=data.get('auth'))

def create_user(self, data: dict):
    # Automatically extracts body and delegates to self.create()
    body = data.get('body', {})
    return self.create(data=body, auth_info=data.get('auth'))
```

#### **Non-CRUD APIs (Custom business logic)**

For APIs that don't follow standard CRUD patterns, inherit from `BaseImplementation`:

```python
from automatic import BaseImplementation

class ReportService(BaseImplementation):
    """Implementation for custom business operations."""
    
    def __init__(self):
        super().__init__()
        # Add your custom initialization here
        self.report_generator = ReportGenerator()
    
    def generate_report(self, data: dict):
        # Custom business logic
        auth_info = data.get('auth')
        body = data.get('body', {})
        
        # Use inherited get_data() method for external data fetching
        try:
            external_data = await self.get_data("analytics", "daily", auth_info)
            report = self.report_generator.create(body, external_data)
            return {"report_id": report.id, "status": "generated"}, 201
        except Exception as e:
            raise ServiceUnavailableError("Report service temporarily unavailable")
```

#### **Manual Implementation (Full control)**

For complete control, implement methods directly without inheritance:

```python
from automatic import NotFoundError, ValidationError, ConflictError

class MyImplementation:
    def create_art_object(self, data: dict) -> tuple[dict, int]:
        # Returns (response_data, status_code)
        return {"id": 1, "title": data["title"]}, 201
    
    def get_art_object(self, data: dict):
        # Auth info is available in data['auth'] if authentication is configured
        auth_info = data.get('auth')
        
        art_id = data["art_id"]
        if art_id not in self.objects:
            raise NotFoundError(f"Art object {art_id} not found")
        return self.objects[art_id], 200
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

2. **Automatic project setup** (recommended):
```bash
# 🚀 Ultimate simplicity - just run automatic!
automatic
# First run: Discovers all specs in current directory, sets up everything
# Subsequent runs: Adds implementations for any new specs

# Or specify a single spec file
automatic my_api.yaml
# Creates: implementations/my_api_service.py (+ project setup if first run)

# Custom output path for single specs
automatic my_api.yaml -o services/user_handler.py

# Example generated CRUD service:
# class UserService(BaseCrudImplementation):
#     resource_name = "user"
#     def get_data_store(self): ...
#     def get_user(self, data): return self.show(...)
#     def create_user(self, data): return self.create(...)
```

3. Use the framework:

**Automatic discovery** (default):
```python
import automatic
# Automatically finds specifications/ and implementations/ directories
app = automatic.create_app()
```

**Explicit specification**:
```python
from automatic import create_app

# With CRUD service
from implementations.user_service import UserService
app = create_app(spec_path="specifications/users.yaml", implementation=UserService())

# With custom service
from implementations.report_service import ReportService
app = create_app(spec_path="specifications/reports.yaml", implementation=ReportService())

# With authentication
from automatic import create_api_key_auth, create_bearer_auth

# API Key authentication
auth = create_api_key_auth(api_keys=['secret-key-123', 'secret-key-456'])
app = create_app(spec_path="specifications/api.yaml", implementation=UserService(), auth_dependency=auth)

# Bearer token authentication
auth = create_bearer_auth(tokens=['token-123', 'token-456'])
app = create_app(spec_path="specifications/api.yaml", implementation=UserService(), auth_dependency=auth)
```

## Automatic Setup

Automatic includes intelligent project setup that discovers and processes your OpenAPI specifications automatically:

### **Smart Discovery Modes**

#### **🚀 First Run Mode** (empty directory)
When you run `automatic` in a directory without existing `specifications/` or `implementations/` directories:

1. **Discovery**: Scans current directory for all OpenAPI specification files (`.yaml`, `.yml`, `.json`)
2. **Validation**: Checks each file to ensure it's a valid OpenAPI spec
3. **Generation**: Creates implementation for each spec using intelligent base class selection
4. **Organization**: Moves specs to `specifications/` directory for clean project structure
5. **Setup**: Creates `main.py` with proper imports and FastAPI configuration
6. **Structure**: Generates `.gitignore` for Python projects

**Example:**
```bash
# Directory with: users.yaml, orders.yaml, products.yaml
automatic

# Results in:
# ├── specifications/
# │   ├── users.yaml
# │   ├── orders.yaml
# │   └── products.yaml
# ├── implementations/
# │   ├── user_service.py
# │   ├── order_service.py
# │   └── product_service.py
# ├── main.py
# └── .gitignore
```

#### **🔄 Incremental Mode** (existing project)
When you run `automatic` in a directory with existing `specifications/` and `implementations/` directories:

1. **Scan**: Checks `specifications/` directory for all spec files
2. **Compare**: Identifies specs that don't have corresponding implementations
3. **Generate**: Creates missing implementations only
4. **Preserve**: Leaves existing files and structure unchanged

**Example:**
```bash
# Add new spec to existing project
cp new_api.yaml specifications/
automatic

# Only creates: implementations/new_api_service.py
```

#### **📋 Single Spec Mode**
When you provide a specific spec file path:

1. **Process**: Generates implementation for the specified file only
2. **Auto-setup**: If first file in empty project, also creates project structure
3. **Custom path**: Supports `-o` flag for custom output location

**Example:**
```bash
automatic my_api.yaml                    # Auto-detects project setup needs
automatic specifications/users.yaml      # Existing project, implementation only
automatic my_api.yaml -o custom/path.py  # Custom output location
```

### **Automatic Base Class Selection**

The generator analyzes your API patterns and chooses the best base class:

- **CRUD APIs** (3+ of: list, show, create, update, delete) → `BaseCrudImplementation`
- **Custom APIs** (non-standard operations) → `BaseImplementation`
- **Manual control** → No base class inheritance

### **CLI Usage**

```bash
# Automatic discovery and setup
automatic                                                # Auto-discover all specs

# Single specification processing  
automatic <spec_path> [-o <output_path>]

# Examples:

# 🚀 Ultimate convenience - zero configuration
automatic                                                # Sets up everything automatically

# Single spec with auto-setup
automatic my_api.yaml                                    # Full project setup if needed

# Custom output path
automatic specifications/users.yaml -o services/users.py  # Custom location

# The generator will ask before overwriting any existing files
```

### **Development Workflows**

#### **Starting a New Project**
```bash
# 1. Create project directory with your OpenAPI specs
mkdir my-project && cd my-project
cp *.yaml .

# 2. One command setup
automatic
# ✅ Complete project structure created
# ✅ All implementations generated
# ✅ main.py configured and ready

# 3. Start developing
python main.py
```

#### **Adding APIs to Existing Project**
```bash
# 1. Add new specification
cp new_api.yaml specifications/

# 2. Generate implementation
automatic
# ✅ Only creates implementations/new_api_service.py
# ✅ Preserves existing code

# 3. Update main.py manually if needed for multi-API setup
```

#### **Iterative Development**
```bash
# 1. Modify your OpenAPI spec
vim specifications/users.yaml

# 2. Regenerate implementation (asks about overwrite)
automatic specifications/users.yaml
# Choose 'y' to overwrite with updated structure

# 3. Re-implement your business logic in the new scaffold
```

### **Intelligent Class Naming**

Generated classes use meaningful names based on the resource:

- `users.yaml` → `UserService`
- `products_v2.yaml` → `ProductsV2Service` 
- `analytics_api.yaml` → `AnalyticsApiService`

No more generic "Implementation" classes that clash!

### **Generated CRUD Service Example**

For a users API with standard CRUD operations:

```python
class UserService(BaseCrudImplementation):
    """CRUD implementation for user resources."""
    
    resource_name = "user"
    
    def get_data_store(self) -> Dict[str, Any]:
        """Return the data storage mechanism."""
        # TODO: Replace with actual database/cache/service connection
        if not hasattr(self, '_data_store'):
            self._data_store = {}
        return self._data_store

    def get_user(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Get a user by ID - delegates to self.show()"""
        resource_id = data.get('user_id')
        if not resource_id:
            raise ValidationError('Resource ID is required')
        return self.show(resource_id, auth_info=data.get('auth'))

    def create_user(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Create a new user - delegates to self.create()"""
        body = data.get('body', {})
        return self.create(data=body, auth_info=data.get('auth'))
    
    # ... update_user, delete_user, list_users methods
```

### **Generated Non-CRUD Service Example**

For custom business operations:

```python
class ReportService(BaseImplementation):
    """Implementation for OpenAPI operations."""
    
    def generate_report(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Generate a new report"""
        auth_info = data.get('auth')
        body = data.get('body', {})
        
        # Use the inherited get_data method for external data fetching:
        # external_data = await self.get_data("resource_type", "resource_id", auth_info)
        
        response_data = {
            "message": "Not implemented yet",
            "operation": "generate_report",
            "received_data": data
        }
        return response_data, 200
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
app = create_app(spec_path="specifications/api.yaml", implementation=MyImpl(), auth_dependency=auth)
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
app = create_app(spec_path="specifications/api.yaml", implementation=MyImpl(), auth_dependency=auth)
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

## Health Check

Automatic automatically adds a `/health` endpoint to every application that provides basic service status:

```json
{
  "status": "healthy",
  "timestamp": "2025-06-20T12:34:56.789Z",
  "service": "automatic"
}
```

**Features**:
- Always returns HTTP 200 with "healthy" status
- Includes current timestamp in ISO format
- No data source dependencies (pure service health)
- Automatically added to all apps

**Usage**: `GET /health`

## Version-Aware Routing

Automatic provides intelligent version handling that allows one implementation to serve multiple API versions. The framework automatically extracts version information and passes it to your handlers.

### **Version Detection**

Versions are automatically extracted from:

1. **Filename patterns**: `users_v1.yaml`, `products_v2.yaml` → versions 1, 2
2. **Operation IDs**: `get_user_v2`, `create_user_v3` → versions 2, 3
3. **Default**: Version 1 if no version pattern is found

### **Version-Aware Implementation**

Generated implementations automatically include `version` parameters:

```python
class UserService(BaseCrudImplementation):
    def get_user(self, data: Dict[str, Any], version: int = 1) -> Tuple[Dict[str, Any], int]:
        """Handle multiple API versions in one method."""
        user_id = data.get('user_id')
        
        # Version-specific logic
        if version == 1:
            # Legacy v1 format
            return {"id": user_id, "name": "John"}, 200
        elif version == 2:
            # Enhanced v2 format  
            return {"id": user_id, "full_name": "John Doe", "metadata": {...}}, 200
        elif version >= 3:
            # Latest format with additional fields
            return {"id": user_id, "profile": {...}, "preferences": {...}}, 200
        else:
            raise ValidationError(f"Unsupported version: {version}")

    def create_user(self, data: Dict[str, Any], version: int = 1) -> Tuple[Dict[str, Any], int]:
        """Version-aware user creation."""
        body = data.get('body', {})
        auth_info = data.get('auth')
        
        if version == 1:
            # Basic validation for v1
            required_fields = ['name', 'email']
        else:
            # Enhanced validation for v2+
            required_fields = ['first_name', 'last_name', 'email', 'phone']
        
        # Apply version-specific validation
        for field in required_fields:
            if field not in body:
                raise ValidationError(f"Missing required field for v{version}: {field}")
        
        return self.create(data=body, auth_info=auth_info)
```

### **Automatic Version Detection and Routing**

The framework automatically:

- **Detects method signatures** - Checks if methods accept `version` parameter
- **Extracts version from routes** - Uses filename and operation ID patterns
- **Passes version to handlers** - Calls `method(data, version=X)` if supported
- **Backward compatibility** - Calls `method(data)` for methods without version parameter

### **Multi-Version Project Structure**

```
project/
├── specifications/
│   ├── users_v1.yaml      # Version 1 API
│   ├── users_v2.yaml      # Version 2 API  
│   └── products_v1.yaml   # Products API
├── implementations/
│   ├── user_service.py    # Handles both v1 and v2
│   └── product_service.py # Handles v1
└── main.py               # Auto-discovery setup
```

### **Version-Specific Operation IDs**

You can also version individual operations:

```yaml
# In users_v1.yaml
paths:
  /users/{id}:
    get:
      operationId: get_user_v2  # This operation uses v2 logic
      # ... rest of spec
```

### **CLI Generation with Versions**

The generator automatically creates version-aware methods:

```bash
# Generates methods with version parameters
automatic specifications/users_v2.yaml

# Generated method signature:
# def get_user(self, data: Dict[str, Any], version: int = 1) -> Tuple[Dict[str, Any], int]:
```

### **Best Practices**

- **Single implementation per resource** - Handle multiple versions in one service class
- **Version-specific logic** - Use `if version == X:` blocks for version differences
- **Progressive enhancement** - Keep v1 simple, add features in higher versions
- **Validation by version** - Apply different validation rules per version
- **Graceful degradation** - Support older versions with reduced functionality

## Examples

Working examples are available in `examples/`:
- `examples/versioning/` - Demonstrates version-aware API handling
- `examples/exceptions/` - Exception handling patterns
- `examples/auth/` - Authentication examples (API key and Bearer token)

## Base Classes Reference

### **BaseCrudImplementation**

Rails-style CRUD base class for standard REST resources:

**Required Methods:**
- `get_data_store()` - Return your data storage mechanism

**Built-in CRUD Methods:**
- `index(filters, auth_info)` - List resources  
- `show(resource_id, auth_info)` - Get single resource
- `create(data, auth_info)` - Create resource
- `update(resource_id, data, auth_info)` - Update resource  
- `destroy(resource_id, auth_info)` - Delete resource

**Customization Hooks:**
- `validate_create(data)` - Custom create validation
- `validate_update(data)` - Custom update validation
- `validate_destroy(resource_id)` - Custom delete validation
- `generate_id(data)` - Custom ID generation
- `build_resource(data, resource_id)` - Custom resource creation
- `merge_updates(existing, updates)` - Custom update merging

### **BaseImplementation**

For non-CRUD APIs with custom business logic:

**Built-in Helper Methods:**
- `get_data(resource_type, resource_id, auth_info)` - External data fetching with error handling

**Usage Pattern:**
- Inherit and implement your custom operation methods
- Use `get_data()` for external service calls
- Follow automatic's exception patterns

## Status

✅ **Core Features Implemented**:
- **Rails-style CRUD base classes** with automatic method delegation
- **Intelligent project setup** with pattern detection and smart class naming
- **Zero-configuration auto-discovery** for seamless multi-API projects
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
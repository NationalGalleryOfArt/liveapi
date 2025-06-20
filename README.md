# automatic

**FastAPI from OpenAPI specs. Zero configuration.**

A Python framework that automatically discovers and creates FastAPI routes from OpenAPI specifications using simple file naming patterns.

## Key Features

- **Zero Configuration**: Just run `automatic.create_app()` - no mapping files needed
- **File-Based Discovery**: File names determine API routes automatically
- **API Versioning**: Single methods handle multiple versions with version parameters
- **Postman Friendly**: Export specs directly from Postman collections
- **Shared Business Logic**: Implementations can easily import and use each other
- **Pure Python Functions**: Clean dict-based interfaces for business logic

## How It Works

```
Directory Structure → Auto-Discovery → FastAPI Routes
```

Your directory structure becomes your API:
```
my-app/
├── api/                    # OpenAPI specs
│   ├── users.yaml         # → /users routes
│   └── orders.yaml        # → /orders routes
├── implementations/        # Business logic
│   ├── users.py           # Standard Implementation class
│   └── orders.py          # Can import users.py
└── main.py
```

## Quick Start

### 1. Zero-config setup
```python
# main.py
import automatic
app = automatic.create_app()  # That's it!
```

### 2. Create your API specs
```yaml
# api/users.yaml
openapi: 3.0.0
info:
  title: Users API
  version: 1.0.0
paths:
  /:
    get:
      operationId: get_users
      responses:
        '200':
          description: List of users
  /{user_id}:
    get:
      operationId: get_user
      parameters:
        - name: user_id
          in: path
          required: true
          schema: {type: integer}
      responses:
        '200':
          description: User details
```

### 3. Implement your business logic
```python
# implementations/users.py
class Implementation:  # Always this name
    def get_users(self, data):
        return [{"id": 1, "name": "Alice"}], 200
    
    def get_user(self, data):
        user_id = data["user_id"]
        return {"id": user_id, "name": "Alice"}, 200
```

### 4. Generated Routes
- `users.yaml` → `/users/` and `/users/{user_id}`
- `orders.yaml` → `/orders/` and `/orders/{order_id}`

**Your API is ready!** Visit http://localhost:8000/docs for interactive documentation.

## Upcoming Features

The following features are planned for future releases:

### Request Validation
- Automatic validation of incoming requests against OpenAPI schema
- Path parameter extraction and typing
- Query parameter handling per OpenAPI spec
- Type coercion and format validation for implementation methods

### Error Handling
- Standard error response format
- Business exception to HTTP status code mapping
- Structured validation error formatting
- Middleware-based error handling

### Response Validation
- Automatic validation of outgoing responses against OpenAPI schema
- Configurable validation modes (strict in development, optional in production)

### Authentication
- API key authentication support
- Authentication context passed to implementation methods
- Flexible middleware-based auth system

### Configuration
- Environment-specific settings
- Flexible configuration options for different deployment scenarios

## Installation

```bash
# Install from source
git clone <repository-url>
cd automatic
pip install -e .
```

## Running Tests

The project uses pytest for testing. Run tests with:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run with coverage (if you have pytest-cov installed)
python -m pytest tests/ --cov=src/automatic -v
```

## Usage Options

### Automatic Discovery (Default)
```python
# Zero config - uses ./api/ and ./implementations/
app = automatic.create_app()

# Custom directories
app = automatic.create_app(api_dir="specs", impl_dir="handlers")
```

## Implementation Interface

Each implementation file contains a standard `Implementation` class with methods matching OpenAPI `operationId` values:

```python
class Implementation:
    def my_operation(self, data: dict) -> tuple[dict, int]:
        """
        Args:
            data: Combined request data (body, path params, query params)
        Returns:
            tuple: (response_data, status_code)
        """
        """
        Example response format:
        {
            "result": "success",
            "error": None,  # Optional error details
            "metadata": {}  # Optional metadata
        }
        """
        return {"result": "success"}, 200
    
    # Version-aware methods (optional)
    def create_user(self, data: dict, version: int = 1) -> tuple[dict, int]:
        """
        Version-aware method handles multiple API versions.
        
        Args:
            data: Combined request data
            version: API version (extracted from filename or operationId)
        Returns:
            tuple: (response_data, status_code)
        """
        if version == 1:
            return {"user_id": data["name"]}, 201
        elif version == 2:
            return {"user_id": data["full_name"], "email": data["email"]}, 201
        else:
            raise UnsupportedVersionError(f"Version {version} not supported")

    def handle_error(self, error: Exception) -> tuple[dict, int]:
        """
        Optional error handler method.
        If present, will be called when an exception occurs.
        
        Args:
            error: The caught exception
        Returns:
            tuple: (error_response, status_code)
        """
        if isinstance(error, ValueError):
            return {"error": str(error)}, 400
        return {"error": "Internal server error"}, 500
```

## Error Handling

Implementations can include an optional `handle_error` method to provide custom error handling:

```python
def handle_error(self, error: Exception) -> tuple[dict, int]:
    """Custom error handling logic"""
    if isinstance(error, ValueError):
        return {"error": str(error)}, 400
    elif isinstance(error, NotFoundError):
        return {"error": "Resource not found"}, 404
    return {"error": "Internal server error"}, 500
```

This allows for:
- Custom error response formatting
- HTTP status code mapping
- Error type-specific handling
- Consistent error responses across endpoints

## Shared Business Logic

Implementations can easily import and use each other:

```python
# implementations/orders.py
class Implementation:
    def create_order(self, data):
        # Import users service
        from .users import Implementation as UserService
        user_service = UserService()
        
        # Validate user exists
        user, status = user_service.get_user({"user_id": data["user_id"]})
        if status != 200:
            return {"error": "User not found"}, 400
            
        return {"order_id": 123, "user_id": data["user_id"]}, 201
```

## Working Example

A complete working example is available in the `examples/convention-demo/` directory:

```bash
# Run the automatic discovery demo
cd examples/convention-demo
python main.py
```

This demonstrates:
- **Zero-config setup**: Just `automatic.create_app()`
- **Multiple APIs**: Users and Orders with shared business logic
- **Path prefixing**: `users.yaml` → `/users/*` routes
- **Inter-service communication**: Orders service validates users

### Example API calls:

```bash
# Users API
curl http://localhost:8000/users
curl http://localhost:8000/users/1
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie"}'

# Orders API (validates users exist)
curl http://localhost:8000/orders
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "total": 75.00}'
```

Visit http://localhost:8000/docs for interactive API documentation.

## API Versioning

Automatic supports clean API versioning where a single method can handle multiple versions:

### Version Detection

The framework automatically extracts version information from:
- **Filenames**: `users_v2.yaml` → version 2
- **OperationIds**: `create_user_v2` → version 2  
- **Default**: version 1 if no version specified

### Version-Aware Implementation

```python
class Implementation:
    def get_user(self, data, version=1):
        user = self._get_user_data(data["user_id"])
        
        if version == 1:
            return {"user_id": user.id, "name": user.name}, 200
        elif version == 2:
            return {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email
            }, 200
        elif version == 3:
            return {
                "user_id": user.id,
                "profile": {
                    "full_name": user.full_name,
                    "email": user.email,
                    "preferences": user.preferences
                }
            }, 200
        else:
            raise UnsupportedVersionError(f"Version {version} not supported")
```

### Versioning Example

A complete versioning example is available in `examples/versioning/`:

```bash
# Run the versioned API example
cd examples/versioning
python run_versioned_example.py
```

Test different versions:
```bash
# v1 API - simple format
curl -X POST "http://localhost:8000/v1/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'

# v2 API - enhanced format  
curl -X POST "http://localhost:8000/v2/users" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Jane Doe", "email": "jane@example.com"}'

# Same user, different response formats
curl "http://localhost:8000/v1/users/1"  # {"user_id": 1, "name": "John"}
curl "http://localhost:8000/v2/users/1"  # {"user_id": 1, "full_name": "John Doe", "email": "john@example.com"}
curl "http://localhost:8000/v3/users/1"  # {"user_id": 1, "profile": {...}}
```

### Benefits

- **DRY Principle**: Single method handles all versions
- **Easy Migration**: Gradual version transitions
- **Clean Deprecation**: Clear error messages for deprecated versions
- **Maintainable**: Version logic contained within implementation
- **Backward Compatible**: Existing methods without version parameters work unchanged

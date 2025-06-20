# automatic

**Convention-based FastAPI from OpenAPI specs. Zero configuration.**

A Python framework that automatically discovers and creates FastAPI routes from OpenAPI specifications using simple file naming conventions.

## Key Features

- **Zero Configuration**: Just run `automatic.create_app()` - no mapping files needed
- **Convention Over Configuration**: File names determine API routes
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

## Usage Modes

### Convention Mode (Recommended)
```python
# Zero config - uses ./api/ and ./implementations/
app = automatic.create_app()

# Custom directories
app = automatic.create_app(api_dir="specs", impl_dir="handlers")
```

### Legacy Mode (Single Spec)
```python
# For existing single-spec projects
app = automatic.create_app("api.yaml", MyImplementation())
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
        return {"result": "success"}, 200
```

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
# Run the convention-based demo
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
# Automatic API Discovery Demo

This demo shows automatic file discovery in the automatic framework.

## Directory Structure

```
convention-demo/
├── api/                    # API specifications
│   ├── users.yaml         # Users API spec
│   └── orders.yaml        # Orders API spec
├── implementations/        # Implementation classes
│   ├── users.py           # Users implementation
│   └── orders.py          # Orders implementation (imports users)
├── main.py                # Demo runner
└── README.md             # This file
```

## How It Works

1. **File Discovery**: Automatic scans `api/` for `*.yaml` files and matches them with `implementations/*.py` files
2. **Path Prefixing**: Each spec file becomes a route prefix:
   - `users.yaml` → `/users` prefix
   - `orders.yaml` → `/orders` prefix
3. **Standard Class Name**: Each implementation file contains a class named `Implementation`
4. **Zero Configuration**: Just run `automatic.create_app()` with no arguments

## Generated Routes

- `GET /users` → `users.py:Implementation.get_users()`
- `GET /users/{user_id}` → `users.py:Implementation.get_user()`
- `POST /users` → `users.py:Implementation.create_user()`
- `GET /orders` → `orders.py:Implementation.get_orders()`
- `GET /orders/{order_id}` → `orders.py:Implementation.get_order()`
- `POST /orders` → `orders.py:Implementation.create_order()`

## Run the Demo

```bash
cd examples/convention-demo
python main.py
```

## Test the API

```bash
# Get all users
curl http://localhost:8000/users

# Get specific user
curl http://localhost:8000/users/1

# Create new user
curl -X POST http://localhost:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name":"Charlie"}'

# Get all orders
curl http://localhost:8000/orders

# Create new order (validates user exists)
curl -X POST http://localhost:8000/orders \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"total":75.00}'
```

## Key Benefits

- **Zero Config**: No mapping files or configuration needed
- **Convention over configuration**: File names determine routes automatically
- **Postman Friendly**: Export specs directly to `api/` directory
- **Shared Code**: Implementations can import and use each other
- **Clean Separation**: API contracts in YAML, business logic in Python
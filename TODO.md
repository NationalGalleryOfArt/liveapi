Simple Convention-Based API
python# Default convention - zero config
app = automatic.create_app()

# Override directories if needed
app = automatic.create_app(
    api_dir="./specs",
    impl_dir="./handlers"
)
File Discovery Convention
Directory structure:
my-app/
├── api/                    # Default API directory
│   ├── users.yaml         # Postman exports this
│   ├── orders.yaml        # Postman exports this
│   └── inventory.yaml
├── implementations/        # Default implementation directory
│   ├── users.py           # Matches users.yaml
│   ├── orders.py          # Matches orders.yaml
│   └── inventory.py
└── main.py
Automatic discovers pairs:

users.yaml → users.py
orders.yaml → orders.py
inventory.yaml → inventory.py

Implementation Class Convention
Standard class name in each file:
python# implementations/users.py
class Implementation:  # Always this name
    def get_user(self, data):
        return {"user_id": data["user_id"]}, 200

# implementations/orders.py  
class Implementation:  # Same class name
    def create_order(self, data):
        # Can import and use other implementations
        from .users import Implementation as Users
        users = Users()
        # ... business logic
        return {"order_id": 123}, 201
Path Prefixing Convention
Filename becomes path prefix:

users.yaml paths get prefixed with /users
orders.yaml paths get prefixed with /orders

Example:
yaml# api/users.yaml (from Postman export)
paths:
  /:
    get:
      operationId: get_users      # Becomes /users/
  /{user_id}:
    get:
      operationId: get_user       # Becomes /users/{user_id}

What automatic does automatically:

Scan api_dir for *.yaml files
For each spec file, look for matching {name}.py in impl_dir
Import {name}.Implementation class
Create FastAPI routes with /{name} prefix
Map operationId to implementation methods
Combine everything into one FastAPI app

What developers do:

Export specs from Postman to ./api/
Create matching implementation files
Write methods that match operationIds
Run automatic.create_app()

No mapping, no configuration, no fuss. Just naming conventions that make sense.
Shared code example:
python# implementations/users.py
class Implementation:
    def get_user(self, data):
        return {"user_id": data["user_id"]}, 200

# implementations/orders.py
class Implementation:
    def create_order(self, data):
        # Just import what you need
        from .users import Implementation as UserService
        user_service = UserService()
        # Use it however you want
        return {"order_id": 123}, 201
The framework stays out of your way. Postman controls the API contract, you write the business logic, automatic connects them. Done.
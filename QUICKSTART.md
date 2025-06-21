# Automatic - Quick Start Guide

Get your API running in 2 simple steps using automatic discovery!

## 🚀 Ultimate Quick Setup

### Step 1: Auto-Generate Everything

Automatic's smart discovery analyzes all your OpenAPI specs and creates complete project structure:

```bash
# 🎯 Ultimate simplicity - just run automatic!
automatic
# Discovers all specs, creates implementations, sets up main.py

# Or specify a single spec
automatic users.yaml

# Custom output path for single specs
automatic users.yaml -o services/user_service.py
```

### 🧠 Intelligent Base Class Selection

The generator automatically chooses the best pattern for your API:

- **CRUD APIs** (with list/show/create/update/delete) → `BaseCrudImplementation`
- **Custom APIs** (non-standard operations) → `BaseImplementation`  
- **Manual control** → No inheritance

Generated implementations include:
- ✅ Smart base class selection based on your OpenAPI operations
- ✅ All OpenAPI operations as methods with proper signatures
- ✅ Built-in CRUD delegation for REST resources
- ✅ Exception handling templates
- ✅ Debug output showing received data
- ✅ Complete project structure with main.py
- ✅ Organized specifications directory

### Step 2: Run Your API

Since automatic created everything, just start the server:

```bash
python main.py
```

The generated `main.py` already includes:
- FastAPI app configuration
- Implementation imports
- uvicorn server setup
- Multi-API support (if multiple specs)

### Test Your API

Your API is now running! The implementations respond with "Not implemented" messages and print all received data to stdout for debugging.

```bash
# Test any endpoint
curl http://localhost:8000/your-endpoint

# You'll see debug output like:
🔄 your_operation called with data: {
  "param1": "value1",
  "body": {...},
  "auth": {...}
}
```

## 📋 What You Get

### For CRUD APIs - BaseCrudImplementation

Automatic CRUD operations with method delegation:

```python
class UserService(BaseCrudImplementation):
    resource_name = "user"
    
    def get_data_store(self):
        return {}  # Your database/storage
    
    def get_user(self, data):
        # Automatically delegates to self.show()
        return self.show(data.get('user_id'), data.get('auth'))
    
    # Built-in CRUD methods available:
    # - self.index(filters, auth_info) - List resources
    # - self.show(resource_id, auth_info) - Get single resource  
    # - self.create(data, auth_info) - Create resource
    # - self.update(resource_id, data, auth_info) - Update resource
    # - self.destroy(resource_id, auth_info) - Delete resource
```

### For Custom APIs - BaseImplementation

Helper methods for external data access:

```python
class ReportService(BaseImplementation):
    def generate_report(self, data):
        # Use inherited get_data() for external calls
        external_data = await self.get_data("analytics", "daily", data.get('auth'))
        
        return {"report_id": "123", "status": "generated"}, 201
```

### Exception Handling Templates
```python
# Access authentication
auth_info = data.get('auth')
if not auth_info:
    raise UnauthorizedError("Authentication required")

# Validate input
if not data.get('required_field'):
    raise ValidationError("Required field missing")

# Handle not found
if resource_id not in self.resources:
    raise NotFoundError(f"Resource {resource_id} not found")

# Handle conflicts
if self.resource_exists(data['name']):
    raise ConflictError("Resource already exists")
```

### Available Exceptions
All exceptions automatically generate proper HTTP responses:

- `ValidationError` → 400 Bad Request
- `UnauthorizedError` → 401 Unauthorized  
- `ForbiddenError` → 403 Forbidden
- `NotFoundError` → 404 Not Found
- `ConflictError` → 409 Conflict
- `RateLimitError` → 429 Too Many Requests
- `ServiceUnavailableError` → 503 Service Unavailable

## 🔐 Adding Authentication

Add authentication when creating your app:

```python
from automatic import create_api_key_auth, create_bearer_auth

# API Key authentication
auth = create_api_key_auth(api_keys=['secret-key-123'])
app = automatic.create_app(auth_dependency=auth)

# Bearer Token authentication  
auth = create_bearer_auth(tokens=['token-123'])
app = automatic.create_app(auth_dependency=auth)
```

Auth info is passed to your methods in `data['auth']`.

## 💡 Development Tips

1. **Start with automatic discovery** - Zero configuration, everything is set up automatically
2. **Use CRUD base classes** - For REST resources, inherit from `BaseCrudImplementation`
3. **Check the debug output** - See exactly what data your methods receive
4. **Implement incrementally** - Override CRUD methods or add custom validation as needed
5. **Use the exceptions** - They automatically generate proper HTTP error responses

## 🎯 Next Steps

1. **For CRUD APIs**: Implement `get_data_store()` with your database/storage
2. **For Custom APIs**: Add business logic using the `get_data()` helper for external calls
3. **Add authentication**: Use the built-in API key or Bearer token auth
4. **Override CRUD methods**: Add custom validation with `validate_create()`, `validate_update()`, etc.
5. **Deploy your API**: Your implementation is ready for production

## 📚 Examples

Check the `examples/` directory for complete working examples:
- `examples/auth/` - Authentication patterns
- `examples/exceptions/` - Exception handling
- `examples/convention-demo/` - Multi-API discovery setup
- `examples/versioning/` - API versioning

---

**That's it!** You now have a fully functional API server with intelligent auto-discovery that chooses the right base class for your API pattern. CRUD resources get automatic method delegation, while custom APIs get helper utilities for external data access.
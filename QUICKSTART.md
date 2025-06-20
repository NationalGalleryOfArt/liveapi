# Automatic - Quick Start Guide

Get your API running in 3 simple steps using the scaffold generator!

## 🚀 Quick Setup

### Step 1: Generate Implementation Scaffold

Generate a Python implementation class from your OpenAPI spec:

```bash
# Generate scaffold from service.yaml -> creates ServiceImplementation class
automatic scaffold service.yaml

# Or specify custom output path  
automatic scaffold service.yaml -o my_implementation.py

# Force overwrite existing file
automatic scaffold service.yaml -f
```

The scaffold generator creates a complete implementation class with:
- ✅ All OpenAPI operations as methods  
- ✅ Detailed docstrings with method signatures
- ✅ Example patterns for common use cases
- ✅ Exception handling templates
- ✅ Debug output showing received data

### Step 2: Run Your API

Create a simple runner script:

```python
# main.py
import automatic

# Automatic finds service.yaml and ServiceImplementation
app = automatic.create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Or be explicit about paths if you prefer:

```python
# main.py  
import automatic
from implementation import ServiceImplementation

app = automatic.create_app(
    spec_path="service.yaml",
    implementation=ServiceImplementation()
)
```

Start your server:
```bash
python main.py
```

### Step 3: Test Your API

Your API is now running! The scaffold responds with "Not implemented" messages and prints all received data to stdout for debugging.

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

The generated implementation includes:

### Method Structure
```python
def your_operation(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Operation summary from OpenAPI spec
    
    Args:
        data: Contains path params, query params, body, and auth info
    
    Returns:
        Tuple of (response_data, status_code)
    """
    # Debug output
    print(f"🔄 your_operation called with data: {json.dumps(data, indent=2)}")
    
    # TODO: Your business logic here
    
    return response_data, 200
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
app = automatic.create_app("api.yaml", ApiImplementation(), auth_dependency=auth)

# Bearer Token authentication  
auth = create_bearer_auth(tokens=['token-123'])
app = automatic.create_app("api.yaml", ApiImplementation(), auth_dependency=auth)
```

Auth info is passed to your methods in `data['auth']`.

## 💡 Development Tips

1. **Start with the scaffold** - It handles all OpenAPI operations and shows you the data structure
2. **Check the debug output** - See exactly what data your methods receive
3. **Implement incrementally** - Replace placeholder responses one method at a time
4. **Use the exceptions** - They automatically generate proper HTTP error responses
5. **Test as you go** - The scaffold makes it easy to test each endpoint immediately

## 🎯 Next Steps

1. Replace placeholder responses with real business logic
2. Add data storage (database, files, etc.)
3. Implement proper authentication checks
4. Add input validation beyond the OpenAPI schema
5. Deploy your API to production

## 📚 Examples

Check the `examples/` directory for complete working examples:
- `examples/auth/` - Authentication patterns
- `examples/exceptions/` - Exception handling
- `examples/convention-demo/` - Multi-API discovery setup
- `examples/versioning/` - API versioning

---

**That's it!** You now have a fully functional API server that responds to all your OpenAPI operations. The scaffold handles the plumbing so you can focus on implementing your business logic.
# API Versioning Example

This example demonstrates how to implement API versioning using the `automatic` framework. The versioning approach allows a single implementation method to handle multiple API versions through a version parameter.

## Key Features

- **Single method per operation**: No need to duplicate methods for different versions
- **Version-aware logic**: Implementation methods receive a version parameter
- **Clean deprecation paths**: Easy to deprecate old versions and guide users to newer ones
- **Automatic version detection**: Framework extracts version from filenames or operationIds

## Files

- `users_v1.yaml` - OpenAPI spec for version 1 (simple user format)
- `users_v2.yaml` - OpenAPI spec for version 2 (enhanced user format)  
- `users_v3.yaml` - OpenAPI spec for version 3 (nested profile format)
- `implementation.py` - Version-aware implementation class
- `run_versioned_example.py` - Runnable server example

## How Versioning Works

### 1. Version Extraction

The framework automatically extracts version information from:

- **Filename**: `users_v2.yaml` → version 2
- **OperationId**: `create_user_v2` → version 2
- **Default**: version 1 if no version specified

### 2. Method Signature Detection

```python
class UserImplementation:
    def create_user(self, data, version=1):  # version parameter detected
        # Version-aware implementation
        if version == 1:
            # Handle v1 format
        elif version == 2:
            # Handle v2 format
```

### 3. Automatic Method Calls

The framework automatically:
- Detects if a method accepts a version parameter
- Calls `method(data, version=X)` if version parameter exists

## Implementation Pattern

```python
class UserImplementation:
    def create_user(self, data, version=1):
        # Normalize input based on version
        if version == 1:
            user_data = self._normalize_v1_input(data)
        elif version == 2:
            user_data = self._normalize_v2_input(data)
        elif version >= 3:
            raise DeprecatedAPIError("v3+ is deprecated")
        
        # Single business logic
        user = self._create_user_in_db(user_data)
        
        # Format output based on version
        if version == 1:
            return {"user_id": user.id}, 201
        elif version == 2:
            return {"user_id": user.id, "email": user.email}, 201
```

## Running the Example

```bash
# Install dependencies
pip install -e .

# Run the versioned API server
python examples/versioning/run_versioned_example.py
```

## Testing Different Versions

Once running, test the different API versions:

```bash
# Create user with v1 API (simple format)
curl -X POST "http://localhost:8000/v1/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'

# Create user with v2 API (enhanced format)
curl -X POST "http://localhost:8000/v2/users" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Jane Doe", "email": "jane@example.com", "phone": "+1234567890"}'

# Get same user with different versions
curl "http://localhost:8000/v1/users/1"  # Simple format
curl "http://localhost:8000/v2/users/1"  # Enhanced format  
curl "http://localhost:8000/v3/users/1"  # Nested profile format
```

## Expected Responses

### v1 GET /users/1
```json
{
  "user_id": 1,
  "name": "John"
}
```

### v2 GET /users/1
```json
{
  "user_id": 1,
  "full_name": "John Doe",
  "email": "john@example.com"
}
```

### v3 GET /users/1
```json
{
  "user_id": 1,
  "profile": {
    "full_name": "John Doe",
    "email": "john@example.com",
    "preferences": {"theme": "dark", "notifications": true}
  }
}
```

## Benefits

1. **DRY Principle**: Single method handles all versions
2. **Easy Migration**: Gradual version transitions
3. **Clean Deprecation**: Clear error messages for deprecated versions
4. **Maintainable**: Version logic contained within implementation
5. **Flexible**: Support for both filename and operationId version specification
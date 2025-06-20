#!/usr/bin/env python3
"""
Example demonstrating API key authentication with automatic.

This example shows how to:
1. Set up API key authentication
2. Apply authentication to all routes
3. Handle authentication in implementation methods
4. Test authenticated and public endpoints

Usage:
    python run_example.py

Test commands:
    # These should fail (401 Unauthorized)
    curl http://localhost:8000/users
    curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name": "John", "email": "john@example.com"}'
    
    # These should work with API key
    curl -H "X-API-Key: secret-key-123" http://localhost:8000/users
    curl -H "X-API-Key: secret-key-456" http://localhost:8000/users
    curl -H "X-API-Key: secret-key-123" -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name": "John", "email": "john@example.com"}'
    
    # Public endpoint (no auth required)
    curl http://localhost:8000/public/health
    
    # Note: Only header-based API keys are supported for security reasons
    # Query parameters and cookies are not recommended for API authentication
"""

import uvicorn
from automatic import create_app, create_api_key_auth
from implementation import Implementation


def main():
    # Create API key authentication
    # Multiple ways to configure API keys:
    
    # 1. Simple list of valid keys
    auth = create_api_key_auth(api_keys=['secret-key-123', 'secret-key-456'])
    
    # 2. Dict with metadata (for more advanced use cases)
    # auth = create_api_key_auth(api_keys={
    #     'admin-key': {'role': 'admin', 'permissions': ['read', 'write', 'delete']},
    #     'readonly-key': {'role': 'readonly', 'permissions': ['read']}
    # })
    
    # 3. Single key
    # auth = create_api_key_auth(api_keys='single-secret-key')
    
    # 4. From environment variable (default: API_KEY)
    # auth = create_api_key_auth()  # Uses os.getenv('API_KEY')
    
    # Create the application with authentication
    app = create_app(
        spec_path="api.yaml",
        implementation=Implementation(),
        auth_dependency=auth,
        title="Authenticated API Example",
        description="Example API demonstrating API key authentication"
    )
    
    print("🔐 Starting authenticated API server...")
    print("🔑 Valid API keys: secret-key-123, secret-key-456")
    print("📍 API docs: http://localhost:8000/docs")
    print("🏥 Health check (public): http://localhost:8000/public/health")
    print("👥 List users (auth required): curl -H 'X-API-Key: secret-key-123' http://localhost:8000/users")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
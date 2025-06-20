#!/usr/bin/env python3
"""
Example demonstrating Bearer token authentication with automatic.

This example shows how to:
1. Set up Bearer token authentication
2. Apply authentication to all routes
3. Test authenticated and public endpoints

Usage:
    python run_bearer_example.py

Test commands:
    # These should fail (401 Unauthorized)
    curl http://localhost:8000/users
    curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name": "John", "email": "john@example.com"}'
    
    # These should work with Bearer token
    curl -H "Authorization: Bearer secret-token-123" http://localhost:8000/users
    curl -H "Authorization: Bearer secret-token-456" http://localhost:8000/users
    curl -H "Authorization: Bearer secret-token-123" -X POST http://localhost:8000/users -H "Content-Type: application/json" -d '{"name": "John", "email": "john@example.com"}'
"""

import uvicorn
from automatic import create_app, create_bearer_auth
from implementation import Implementation


def main():
    # Create Bearer token authentication
    # Multiple ways to configure tokens:
    
    # 1. Simple list of valid tokens
    auth = create_bearer_auth(tokens=['secret-token-123', 'secret-token-456'])
    
    # 2. Dict with metadata (for more advanced use cases)
    # auth = create_bearer_auth(tokens={
    #     'admin-token': {'role': 'admin', 'permissions': ['read', 'write', 'delete']},
    #     'readonly-token': {'role': 'readonly', 'permissions': ['read']}
    # })
    
    # 3. Single token
    # auth = create_bearer_auth(tokens='single-secret-token')
    
    # 4. From environment variable (default: BEARER_TOKEN)
    # auth = create_bearer_auth()  # Uses os.getenv('BEARER_TOKEN')
    
    # Create the application with authentication
    app = create_app(
        spec_path="api.yaml",
        implementation=Implementation(),
        auth_dependency=auth,
        title="Bearer Token API Example",
        description="Example API demonstrating Bearer token authentication"
    )
    
    print("🔐 Starting Bearer token authenticated API server...")
    print("🎫 Valid tokens: secret-token-123, secret-token-456")
    print("📍 API docs: http://localhost:8000/docs")
    print("👥 List users (auth required): curl -H 'Authorization: Bearer secret-token-123' http://localhost:8000/users")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
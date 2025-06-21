"""Example demonstrating versioned API implementation."""

import sys
import os
import uvicorn
from fastapi import FastAPI
from automatic.app import create_app
from implementation import UserImplementation

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


def main():
    """Run versioned API example."""
    print("Starting versioned API example...")
    print("This example demonstrates version-aware API implementation:")
    print("- v1: Simple user creation and retrieval")
    print("- v2: Enhanced user data with full names and email")
    print("- v3: Nested profile structure for user data")
    print()

    # Create implementation
    impl = UserImplementation()

    # Create three separate apps for different versions
    app_v1 = create_app("examples/versioning/users_v1.yaml", impl)
    app_v2 = create_app("examples/versioning/users_v2.yaml", impl)
    app_v3 = create_app("examples/versioning/users_v3.yaml", impl)

    # Combine them into a single app with version prefixes
    main_app = FastAPI(title="Versioned Users API", version="1.0.0")

    # Mount version-specific apps
    main_app.mount("/v1", app_v1)
    main_app.mount("/v2", app_v2)
    main_app.mount("/v3", app_v3)

    @main_app.get("/")
    async def root():
        return {
            "message": "Versioned Users API",
            "versions": {
                "v1": {
                    "endpoints": [
                        "POST /v1/users - Create user (simple format)",
                        "GET /v1/users/{user_id} - Get user (name only)",
                    ]
                },
                "v2": {
                    "endpoints": [
                        "POST /v2/users - Create user (enhanced format)",
                        "GET /v2/users/{user_id} - Get user (full details)",
                    ]
                },
                "v3": {
                    "endpoints": ["GET /v3/users/{user_id} - Get user (nested profile)"]
                },
            },
            "test_commands": [
                "# Create user with v1 API:",
                'curl -X POST "http://localhost:8000/v1/users" -H "Content-Type: application/json" -d \'{"name": "John", "email": "john@example.com"}\'',
                "",
                "# Create user with v2 API:",
                'curl -X POST "http://localhost:8000/v2/users" -H "Content-Type: application/json" -d \'{"full_name": "Jane Doe", "email": "jane@example.com", "phone": "+1234567890"}\'',
                "",
                "# Get user with different versions:",
                'curl "http://localhost:8000/v1/users/1"',
                'curl "http://localhost:8000/v2/users/1"',
                'curl "http://localhost:8000/v3/users/1"',
            ],
        }

    print("API endpoints:")
    print("- GET / - API documentation and test commands")
    print("- POST /v1/users - Create user (v1 format)")
    print("- GET /v1/users/{id} - Get user (v1 format)")
    print("- POST /v2/users - Create user (v2 format)")
    print("- GET /v2/users/{id} - Get user (v2 format)")
    print("- GET /v3/users/{id} - Get user (v3 format)")
    print()
    print("Starting server on http://localhost:8000")
    print("Visit http://localhost:8000 for test commands")

    uvicorn.run(main_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

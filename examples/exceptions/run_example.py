"""Run the exception handling example."""

import uvicorn
from automatic import create_app
from implementation import UserService


def main():
    # Create implementation
    implementation = UserService()

    # Create app using modern API
    app = create_app(
        spec_path="users.yaml",
        implementation=implementation,
        title="User API with Exception Handling",
        description="Demonstrates automatic exception to HTTP response mapping",
    )

    print("Starting server with exception handling example...")
    print("Try these commands:")
    print()
    print("# Get existing user:")
    print("curl http://localhost:8000/users/1")
    print()
    print("# Get non-existent user (404):")
    print("curl http://localhost:8000/users/999")
    print()
    print("# Create user with invalid email (400):")
    print(
        'curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d \'{"username": "test", "email": "invalid"}\''
    )
    print()
    print("# Create duplicate user (409):")
    print(
        'curl -X POST http://localhost:8000/users -H "Content-Type: application/json" -d \'{"username": "admin", "email": "new@example.com"}\''
    )
    print()
    print("# Try to delete admin (403):")
    print("curl -X DELETE http://localhost:8000/users/1")
    print()

    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

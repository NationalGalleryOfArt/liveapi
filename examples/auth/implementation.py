"""Implementation for authenticated API example."""

from typing import Dict, Any
from datetime import datetime
from automatic import NotFoundError, ConflictError, ValidationError


class UserService:
    """Implementation class for the authenticated API."""

    def __init__(self):
        # Simple in-memory user storage
        self.users = {}
        self.user_counter = 1

    def list_users(self, data: Dict[str, Any]) -> list:
        """List all users (requires authentication)."""
        # Auth info is available in data['auth'] if authentication passed
        auth_info = data.get("auth")
        if not auth_info:
            raise Exception("Authentication required")

        users_list = list(self.users.values())
        return users_list  # Status code automatically inferred (GET=200)

    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user (requires authentication)."""
        # Auth info is available in data['auth'] if authentication passed
        auth_info = data.get("auth")
        if not auth_info:
            raise Exception("Authentication required")

        name = data.get("name")
        email = data.get("email")

        if not name or not email:
            raise ValidationError("Name and email are required")

        # Check if user already exists
        for user in self.users.values():
            if user["email"] == email:
                raise ConflictError(f"User with email {email} already exists")

        # Create new user
        user_id = str(self.user_counter)
        self.user_counter += 1

        user = {
            "id": user_id,
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat(),
        }

        self.users[user_id] = user
        return user  # Status code automatically inferred (POST=201)

    def get_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a user by ID (requires authentication)."""
        # Auth info is available in data['auth'] if authentication passed
        auth_info = data.get("auth")
        if not auth_info:
            raise Exception("Authentication required")

        user_id = data.get("user_id")
        if not user_id:
            raise ValidationError("User ID is required")

        if user_id not in self.users:
            raise NotFoundError(f"User {user_id} not found")

        return self.users[user_id]  # Status code automatically inferred (GET=200)

    def health_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Public health check (no authentication required)."""
        # This endpoint doesn't require authentication
        # Note: auth info may or may not be present in data['auth']
        return {"status": "healthy"}  # Status code automatically inferred (GET=200)

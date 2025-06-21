"""Example implementation demonstrating exception handling."""

from automatic import NotFoundError, ValidationError, ConflictError, ForbiddenError


class UserImplementation:
    """User API implementation with exception handling."""

    def __init__(self):
        # Simple in-memory user store
        self.users = {
            1: {"id": 1, "username": "admin", "email": "admin@example.com"},
            2: {"id": 2, "username": "user1", "email": "user1@example.com"},
        }
        self.next_id = 3

    def get_user(self, data):
        """Get user by ID."""
        user_id = int(data["user_id"])

        if user_id not in self.users:
            # This exception automatically becomes a 404 response
            raise NotFoundError(
                f"User with ID {user_id} not found", extra={"requested_id": user_id}
            )

        return self.users[user_id], 200

    def create_user(self, data):
        """Create new user."""
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()

        # Validate input
        if not username:
            raise ValidationError("Username cannot be empty")

        if "@" not in email:
            raise ValidationError("Invalid email format", extra={"email": email})

        # Check for duplicates
        for user in self.users.values():
            if user["username"] == username:
                raise ConflictError(
                    f"Username '{username}' already exists",
                    extra={"existing_user_id": user["id"]},
                )
            if user["email"] == email:
                raise ConflictError(
                    f"Email '{email}' already registered",
                    extra={"existing_user_id": user["id"]},
                )

        # Create user
        new_user = {"id": self.next_id, "username": username, "email": email}
        self.users[self.next_id] = new_user
        self.next_id += 1

        return new_user, 201

    def delete_user(self, data):
        """Delete user by ID."""
        user_id = int(data["user_id"])

        if user_id not in self.users:
            raise NotFoundError(f"User with ID {user_id} not found")

        # Don't allow deleting admin
        if self.users[user_id]["username"] == "admin":
            raise ForbiddenError(
                "Cannot delete admin user",
                extra={"user_id": user_id, "username": "admin"},
            )

        del self.users[user_id]
        return {}, 204  # No content

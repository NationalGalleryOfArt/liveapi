"""Version-aware user implementation."""


class UnsupportedVersionError(Exception):
    """Raised when an unsupported API version is requested."""

    pass


class DeprecatedAPIError(Exception):
    """Raised when a deprecated API version is used."""

    pass


class UserService:
    """Implementation class with version-aware methods."""

    def __init__(self):
        # Mock user database
        self.users = {
            1: {
                "id": 1,
                "name": "John",
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "preferences": {"theme": "dark", "notifications": True},
            },
            2: {
                "id": 2,
                "name": "Jane",
                "full_name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "+0987654321",
                "preferences": {"theme": "light", "notifications": False},
            },
        }
        self.next_id = 3

    def create_user(self, data, version=1):
        """Create a new user with version-aware input/output handling."""
        user_data = {}

        if version == 1:
            # v1 input format: {"name": "John", "email": "john@example.com"}
            user_data = {
                "id": self.next_id,
                "name": data["name"],
                "full_name": data["name"],  # Convert v1 to internal format
                "email": data.get("email", ""),
                "phone": "",
                "preferences": {},
            }
        elif version == 2:
            # v2 input format: {"full_name": "John Doe", "email": "john@example.com", "phone": "+123"}
            user_data = {
                "id": self.next_id,
                "name": data["full_name"].split()[
                    0
                ],  # Extract first name for backward compat
                "full_name": data["full_name"],
                "email": data["email"],
                "phone": data.get("phone", ""),
                "preferences": {},
            }
        elif version >= 3:
            raise DeprecatedAPIError("create_user v3+ is deprecated. Use v2.")
        else:
            raise UnsupportedVersionError(f"Version {version} not supported")

        # Store user
        self.users[self.next_id] = user_data
        self.next_id += 1

        # Format output based on version
        if version == 1:
            return {"user_id": user_data["id"]}, 201
        elif version == 2:
            return {"user_id": user_data["id"], "email": user_data["email"]}, 201

    def get_user(self, data, version=1):
        """Get user with version-aware output formatting."""
        user_id = int(data["user_id"])

        if user_id not in self.users:
            return {"error": "User not found"}, 404

        user = self.users[user_id]

        if version == 1:
            # v1 output format: simple user info
            return {"user_id": user["id"], "name": user["name"]}, 200
        elif version == 2:
            # v2 output format: enhanced user info
            return {
                "user_id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"],
            }, 200
        elif version == 3:
            # v3 output format: nested profile structure
            return {
                "user_id": user["id"],
                "profile": {
                    "full_name": user["full_name"],
                    "email": user["email"],
                    "preferences": user["preferences"],
                },
            }, 200
        else:
            raise UnsupportedVersionError(f"Version {version} not supported")

"""User management implementation."""

# In-memory storage for demo
users_db = {
    1: {"user_id": 1, "name": "Alice"},
    2: {"user_id": 2, "name": "Bob"}
}
next_user_id = 3


class Implementation:
    """Standard implementation class for users API."""
    
    def get_users(self, data):
        """Get all users."""
        return list(users_db.values()), 200
    
    def get_user(self, data):
        """Get user by ID."""
        user_id = int(data["user_id"])
        
        if user_id in users_db:
            return users_db[user_id], 200
        else:
            return {"error": "User not found"}, 404
    
    def create_user(self, data):
        """Create a new user."""
        global next_user_id
        
        new_user = {
            "user_id": next_user_id,
            "name": data["name"]
        }
        
        users_db[next_user_id] = new_user
        next_user_id += 1
        
        return new_user, 201
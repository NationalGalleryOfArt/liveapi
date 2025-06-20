"""Order management implementation."""

# In-memory storage for demo
orders_db = {
    1: {"order_id": 1, "user_id": 1, "total": 99.99},
    2: {"order_id": 2, "user_id": 2, "total": 149.50}
}
next_order_id = 3


class Implementation:
    """Standard implementation class for orders API."""
    
    def get_orders(self, data):
        """Get all orders."""
        return list(orders_db.values()), 200
    
    def get_order(self, data):
        """Get order by ID."""
        order_id = int(data["order_id"])
        
        if order_id in orders_db:
            return orders_db[order_id], 200
        else:
            return {"error": "Order not found"}, 404
    
    def create_order(self, data):
        """Create a new order."""
        global next_order_id
        
        # Import and use user service to validate user exists
        from .users import Implementation as UserService
        user_service = UserService()
        
        # Check if user exists
        user_result, status = user_service.get_user({"user_id": data["user_id"]})
        if status != 200:
            return {"error": "User not found"}, 400
        
        new_order = {
            "order_id": next_order_id,
            "user_id": data["user_id"],
            "total": data["total"]
        }
        
        orders_db[next_order_id] = new_order
        next_order_id += 1
        
        return new_order, 201
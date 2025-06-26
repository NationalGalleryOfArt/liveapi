# SQLModelResource Hook-Based Architecture

## Overview

LiveAPI's SQLModelResource now features a powerful hook-based architecture that allows developers to customize database resource behavior without overriding entire CRUD methods. This design follows the Template Method pattern, providing clean extension points for common customization needs.

## Architecture

The refactored architecture consists of:

1. **BaseSQLModelResource** - Abstract base class containing core CRUD logic and hook definitions
2. **SQLModelResource** - Concrete class that users subclass, inheriting all base functionality
3. **Hook Methods** - Extension points for customizing behavior at specific lifecycle stages

## Hook Methods

### Data Transformation Hooks

These hooks allow you to transform data between API and database formats:

#### `to_dto(db_resource: SQLModel) -> Dict[str, Any]`

Transform database models to API-friendly dictionaries (DTOs).

**Use cases:**
- Rename fields for API consistency
- Add computed fields
- Format dates and times
- Hide internal fields
- Convert data types (e.g., decimals to integers)

**Example:**
```python
def to_dto(self, db_resource: Product) -> Dict[str, Any]:
    return {
        "id": db_resource.id,
        "productName": db_resource.name,  # Rename field
        "priceInCents": int(db_resource.price * 100),  # Convert to cents
        "isAvailable": db_resource.stock > 0,  # Computed field
        "createdAt": db_resource.created_at.isoformat()
    }
```

#### `from_api(data: Dict[str, Any]) -> Dict[str, Any]`

Transform incoming API data to database format.

**Use cases:**
- Map API field names to database columns
- Convert data types
- Parse nested objects
- Handle optional fields properly

**Example:**
```python
def from_api(self, data: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    if "productName" in data:
        result["name"] = data["productName"]
    if "priceInCents" in data:
        result["price"] = data["priceInCents"] / 100.0
    if "address" in data:
        # Parse nested object
        result["street"] = data["address"].get("street")
        result["city"] = data["address"].get("city")
    return result
```

### Lifecycle Hooks

These hooks are called at specific points in the CRUD lifecycle:

#### `before_create(data: Dict[str, Any]) -> Dict[str, Any]`

Called before creating a new resource.

**Use cases:**
- Validate business rules
- Set default values
- Generate slugs or codes
- Normalize data
- Check permissions

**Example:**
```python
async def before_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
    # Validation
    if not data.get("name"):
        raise ValidationError("Name is required")
    
    # Set defaults
    if "status" not in data:
        data["status"] = "draft"
    
    # Generate slug
    data["slug"] = data["name"].lower().replace(" ", "-")
    
    # Set owner
    data["created_by"] = get_current_user_id()
    
    return data
```

#### `after_create(resource: SQLModel) -> None`

Called after successfully creating a resource.

**Use cases:**
- Send notifications
- Update caches
- Create related records
- Trigger workflows
- Log events

**Example:**
```python
async def after_create(self, resource: Product) -> None:
    # Send notification
    await send_email(f"New product created: {resource.name}")
    
    # Clear cache
    await redis_client.delete("products:list")
    
    # Create audit log
    await create_audit_log("create", resource.id, resource.model_dump())
    
    # Trigger external webhook
    await trigger_webhook("product.created", resource)
```

#### `before_update(resource_id: Any, data: Dict[str, Any]) -> Dict[str, Any]`

Called before updating a resource.

**Use cases:**
- Validate update permissions
- Check business rules
- Track changes
- Prevent certain updates
- Add metadata

**Example:**
```python
async def before_update(self, resource_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
    # Check current state
    existing = await self.read(resource_id)
    
    # Prevent status changes in certain states
    if existing["status"] == "published" and "status" in data:
        raise ValidationError("Cannot change status of published items")
    
    # Track who made changes
    data["updated_by"] = get_current_user_id()
    
    # Validate price changes
    if "price" in data:
        old_price = existing["price"]
        new_price = data["price"]
        if abs(new_price - old_price) > old_price * 0.5:
            data["requires_approval"] = True
    
    return data
```

#### `after_update(resource: SQLModel) -> None`

Called after successfully updating a resource.

**Use cases:**
- Invalidate caches
- Sync with external systems
- Send notifications
- Update search indices

**Example:**
```python
async def after_update(self, resource: Product) -> None:
    # Invalidate specific cache
    await redis_client.delete(f"product:{resource.id}")
    
    # Update search index
    await search_client.index_document("products", resource.id, resource.model_dump())
    
    # Sync with external inventory system
    if resource.stock_changed:
        await sync_inventory_system(resource)
```

#### `before_delete(resource_id: Any) -> None`

Called before deleting a resource.

**Use cases:**
- Check for dependencies
- Prevent deletion based on state
- Archive instead of delete
- Validate permissions

**Example:**
```python
async def before_delete(self, resource_id: Any) -> None:
    # Check for active orders
    orders = await db.query("SELECT COUNT(*) FROM orders WHERE product_id = ?", resource_id)
    if orders > 0:
        raise ValidationError("Cannot delete product with active orders")
    
    # Archive the resource
    resource = await self.read(resource_id)
    await archive_service.archive("products", resource)
    
    # Check permissions
    if not has_permission("products.delete"):
        raise ValidationError("Insufficient permissions")
```

#### `after_delete(resource_id: Any) -> None`

Called after successfully deleting a resource.

**Use cases:**
- Clean up related data
- Remove from caches
- Update statistics
- Trigger cascading deletes

**Example:**
```python
async def after_delete(self, resource_id: Any) -> None:
    # Clean up images
    await storage_service.delete_folder(f"products/{resource_id}")
    
    # Remove from all caches
    await redis_client.delete(f"product:{resource_id}")
    await redis_client.delete("products:list")
    
    # Update statistics
    await stats_service.decrement("products.count")
```

### Query Hooks

#### `build_list_query(query: select, filters: Dict[str, Any]) -> select`

Customize the query used for listing resources.

**Use cases:**
- Add default ordering
- Implement custom filters
- Add joins for related data
- Apply security filters
- Implement full-text search

**Example:**
```python
def build_list_query(self, query: select, filters: Dict[str, Any]) -> select:
    # Add search functionality
    if "search" in filters:
        search_term = filters.pop("search")
        query = query.where(
            or_(
                Product.name.contains(search_term),
                Product.description.contains(search_term),
                Product.sku.contains(search_term)
            )
        )
    
    # Filter by availability
    if "available" in filters:
        is_available = filters.pop("available")
        if is_available:
            query = query.where(Product.stock > 0)
        else:
            query = query.where(Product.stock == 0)
    
    # Add joins for category names
    query = query.join(Category).options(selectinload(Product.category))
    
    # Default ordering
    query = query.order_by(Product.created_at.desc())
    
    # Apply remaining filters
    return super().build_list_query(query, filters)
```

## Complete Example

Here's a complete example showing how to implement a production-ready resource with all hooks:

```python
from typing import Any, Dict, List
from datetime import datetime
from sqlmodel import Session, select, or_
from sqlalchemy.orm import selectinload

from liveapi.implementation.sql_model_resource import SQLModelResource
from liveapi.implementation.exceptions import ValidationError
from .models import Product, Category
from .services import cache, search, notifications, audit


class ProductResource(SQLModelResource):
    """Production-ready product resource with full hook implementation."""
    
    def __init__(self, session: Session):
        super().__init__(model=Product, resource_name="products", session=session)
    
    # Data transformation
    def to_dto(self, db_resource: Product) -> Dict[str, Any]:
        """Transform to API format with custom fields."""
        return {
            "id": db_resource.id,
            "sku": db_resource.sku,
            "displayName": db_resource.name,
            "description": db_resource.description,
            "priceInCents": int(db_resource.price * 100),
            "category": {
                "id": db_resource.category.id,
                "name": db_resource.category.name
            } if db_resource.category else None,
            "stock": {
                "quantity": db_resource.stock_quantity,
                "status": self._get_stock_status(db_resource.stock_quantity)
            },
            "images": [img.url for img in db_resource.images],
            "isAvailable": db_resource.is_active and db_resource.stock_quantity > 0,
            "createdAt": db_resource.created_at.isoformat(),
            "updatedAt": db_resource.updated_at.isoformat()
        }
    
    def from_api(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform from API format to database format."""
        result = {}
        
        # Basic field mapping
        field_map = {
            "displayName": "name",
            "priceInCents": ("price", lambda x: x / 100.0),
            "description": "description",
            "sku": "sku"
        }
        
        for api_field, db_field in field_map.items():
            if api_field in data:
                if isinstance(db_field, tuple):
                    field_name, transform = db_field
                    result[field_name] = transform(data[api_field])
                else:
                    result[db_field] = data[api_field]
        
        # Handle nested objects
        if "category" in data:
            result["category_id"] = data["category"].get("id")
        
        if "stock" in data:
            result["stock_quantity"] = data["stock"].get("quantity", 0)
        
        return result
    
    # Lifecycle hooks
    async def before_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and prepare product for creation."""
        # Required field validation
        required_fields = ["name", "sku", "price"]
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f"{field} is required")
        
        # SKU uniqueness check
        existing = self.session.exec(
            select(Product).where(Product.sku == data["sku"])
        ).first()
        if existing:
            raise ValidationError(f"SKU {data['sku']} already exists")
        
        # Price validation
        if data.get("price", 0) < 0:
            raise ValidationError("Price cannot be negative")
        
        # Set defaults
        data.setdefault("stock_quantity", 0)
        data.setdefault("is_active", True)
        
        # Generate search keywords
        data["search_keywords"] = self._generate_keywords(data)
        
        return data
    
    async def after_create(self, resource: Product) -> None:
        """Handle post-creation tasks."""
        # Update search index
        await search.index_product(resource)
        
        # Clear caches
        await cache.delete_pattern("products:*")
        
        # Send notifications
        if resource.stock_quantity == 0:
            await notifications.notify_low_stock(resource)
        
        # Create audit log
        await audit.log("product.created", resource.id, {"sku": resource.sku})
    
    async def before_update(self, resource_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate updates and track changes."""
        existing = await self.read(resource_id)
        
        # Prevent SKU changes
        if "sku" in data and data["sku"] != existing["sku"]:
            raise ValidationError("SKU cannot be changed")
        
        # Track price changes
        if "price" in data:
            old_price = existing["priceInCents"] / 100.0
            new_price = data["price"]
            if abs(new_price - old_price) > old_price * 0.5:
                # Require approval for large price changes
                data["pending_approval"] = True
                await notifications.notify_price_change_approval(resource_id, old_price, new_price)
        
        # Update search keywords if name changes
        if "name" in data:
            data["search_keywords"] = self._generate_keywords(data)
        
        return data
    
    async def after_update(self, resource: Product) -> None:
        """Handle post-update tasks."""
        # Update search index
        await search.update_product(resource)
        
        # Invalidate specific caches
        await cache.delete(f"product:{resource.id}")
        await cache.delete_pattern("products:list:*")
        
        # Check stock levels
        if resource.stock_quantity <= 5:
            await notifications.notify_low_stock(resource)
    
    async def before_delete(self, resource_id: Any) -> None:
        """Validate deletion is allowed."""
        product = self.session.get(Product, resource_id)
        
        # Check for active orders
        active_orders = await self._count_active_orders(resource_id)
        if active_orders > 0:
            raise ValidationError(f"Cannot delete product with {active_orders} active orders")
        
        # Archive product data
        await audit.archive_product(product)
    
    async def after_delete(self, resource_id: Any) -> None:
        """Clean up after deletion."""
        # Remove from search index
        await search.remove_product(resource_id)
        
        # Clear all caches
        await cache.delete_pattern(f"product:{resource_id}:*")
        await cache.delete_pattern("products:*")
        
        # Clean up storage
        await storage.delete_folder(f"products/{resource_id}")
    
    def build_list_query(self, query: select, filters: Dict[str, Any]) -> select:
        """Build advanced listing query."""
        # Full-text search
        if "q" in filters:
            search_term = filters.pop("q")
            query = query.where(
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%"),
                    Product.sku.ilike(f"%{search_term}%"),
                    Product.search_keywords.contains([search_term])
                )
            )
        
        # Price range filter
        if "min_price" in filters:
            min_price = filters.pop("min_price")
            query = query.where(Product.price >= min_price)
        
        if "max_price" in filters:
            max_price = filters.pop("max_price")
            query = query.where(Product.price <= max_price)
        
        # Availability filter
        if "available" in filters:
            is_available = filters.pop("available")
            if is_available:
                query = query.where(Product.stock_quantity > 0, Product.is_active == True)
            else:
                query = query.where(or_(Product.stock_quantity == 0, Product.is_active == False))
        
        # Category filter with join
        if "category_id" in filters:
            query = query.join(Category)
        
        # Include related data
        query = query.options(
            selectinload(Product.category),
            selectinload(Product.images)
        )
        
        # Default ordering
        order_by = filters.pop("order_by", "created_at")
        order_dir = filters.pop("order_dir", "desc")
        
        order_map = {
            "name": Product.name,
            "price": Product.price,
            "created_at": Product.created_at,
            "stock": Product.stock_quantity
        }
        
        if order_by in order_map:
            order_field = order_map[order_by]
            query = query.order_by(
                order_field.desc() if order_dir == "desc" else order_field
            )
        
        # Apply remaining filters
        return super().build_list_query(query, filters)
    
    # Helper methods
    def _get_stock_status(self, quantity: int) -> str:
        if quantity == 0:
            return "out_of_stock"
        elif quantity <= 5:
            return "low_stock"
        else:
            return "in_stock"
    
    def _generate_keywords(self, data: Dict[str, Any]) -> List[str]:
        """Generate search keywords from product data."""
        keywords = []
        if "name" in data:
            keywords.extend(data["name"].lower().split())
        if "description" in data:
            keywords.extend(data["description"].lower().split()[:20])
        return list(set(keywords))
    
    async def _count_active_orders(self, product_id: str) -> int:
        """Count active orders for a product."""
        # Implementation depends on your order system
        return 0
```

## Best Practices

1. **Keep Hooks Focused**: Each hook should have a single responsibility
2. **Use Appropriate Exceptions**: Raise `ValidationError` for business rule violations
3. **Handle Partial Updates**: Remember that `from_api` is called for both creates and updates
4. **Avoid Heavy Operations**: Keep synchronous hooks fast; use background tasks for heavy work
5. **Test Your Hooks**: Write unit tests for each hook method
6. **Document Custom Behavior**: Add docstrings explaining why each hook exists

## Migration Guide

If you have existing SQLModelResource subclasses, migration is straightforward:

1. Remove any overridden CRUD methods (`create`, `update`, etc.)
2. Extract validation logic into `before_*` hooks
3. Extract post-operation logic into `after_*` hooks
4. Move data transformation into `to_dto` and `from_api`
5. Move query customization into `build_list_query`

The hook-based approach will make your code cleaner, more testable, and easier to maintain.
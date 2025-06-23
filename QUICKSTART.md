# LiveAPI Quick Start Guide

Get up and running with LiveAPI in 5 minutes.

## Prerequisites

- Python 3.13+
- pip

## Installation

```bash
git clone <repository-url>
cd liveapi
pip install -e .
```

## 5-Minute Tutorial

### Step 1: Initialize Your Project
```bash
mkdir my-api
cd my-api
liveapi init
```

### Step 2: Generate an API Specification
You can either generate a spec interactively, or create one manually.

**Option A: Interactive Generation (Recommended)**
```bash
liveapi generate
```
Follow the interactive prompts to define your API.

**Option B: Manual Creation**
Create a file named `specifications/users.yaml` with your OpenAPI content.

### Step 3: Generate Implementation Files
```bash
liveapi sync
```
This will generate:
- `implementations/users_service.py` - Customizable service class with database hooks
- `main.py` - FastAPI application that loads your service

The generated service class contains CRUD method overrides ready for database integration.

### Step 4: Run Your API
```bash
liveapi run
```

### Step 5: Test Your API
```bash
curl http://localhost:8000/health
# Assuming you created a 'users' API
curl http://localhost:8000/users
```

### Step 6: View Interactive Docs
Open your browser to `http://localhost:8000/docs` to see the Swagger UI.

## Making Changes

### Option 1: Edit Your Spec
1.  **Edit your spec**: Modify your `users.yaml` file to add a new endpoint or change an existing one.
2.  **Check what changed**: Run `liveapi status` to see a summary of your changes.
3.  **Create a new version**: Run `liveapi version create --minor` to create a new, versioned spec file.
4.  **Update your implementation**: Run `liveapi sync` to regenerate service files with changes.

### Option 2: Customize Your Database Implementation
1.  **Edit service class**: Open `implementations/users_service.py`
2.  **Add database connection**: Replace the TODO comments with your database code
3.  **Add business logic**: Implement validation, logging, caching as needed
4.  **Test changes**: Your customizations are preserved across spec updates

Example database integration:
```python
async def create_user(self, user_data: dict) -> dict:
    # Replace TODO with your database insert
    result = await self.db.insert_one("users", {
        "id": str(uuid.uuid4()),
        **user_data,
        "created_at": datetime.utcnow()
    })
    return result
```

## Stop the Development Server

When you're done, you can stop the server with:
```bash
liveapi kill
```

## What's Next?

### Learn More Commands
- `liveapi version list` - List all API versions
- `liveapi version compare v1.0.0 v1.1.0` - Compare version changes
- `liveapi sync --preview` - Preview sync changes without applying them
- `liveapi sync --crud` - Use legacy dynamic CRUD+ mode

### Customize Your Implementation
- **Database Integration**: Replace in-memory storage with PostgreSQL, MongoDB, etc.
- **Business Logic**: Add validation, authorization, logging, caching
- **Error Handling**: Customize ValidationError and ConflictError responses
- **Custom Endpoints**: Add non-CRUD endpoints alongside generated ones

### Production Deployment
- Your generated service classes are production-ready
- Database connections, logging, and error handling are built-in
- Service classes can be version controlled and customized independently
- Use container deployment with your customized implementations

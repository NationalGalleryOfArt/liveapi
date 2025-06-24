# LiveAPI Quick Start Guide

Get up and running with LiveAPI in 5 minutes. This guide covers setup, basic usage, and customization.

## Prerequisites

- Python 3.13+
- pip

## Installation

```bash
git clone <repository-url>
cd liveapi
pip install -e .
```

## Tutorial

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
Follow the interactive prompts to define your API:
1. Enter your object name (e.g., "users")
2. Describe your object (e.g., "User management records")
3. Choose your backend:
   - **1**: DefaultResourceService (In-memory, for prototypes)  
   - **2**: SQLModelResourceService (PostgreSQL, for production)
4. Provide JSON schema and examples

**Option B: Manual Creation**
Create a file named `specifications/users.yaml` with your OpenAPI content.

### Step 3: Configure Database (SQL Backend Only)
If you chose SQLModelResourceService in step 2, set up your database:

```bash
# For PostgreSQL (recommended for production)
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"

# For SQLite (default for development)  
export DATABASE_URL="sqlite:///./myapi.db"

# Install SQL dependencies
pip install sqlmodel psycopg2-binary
```

### Step 4: Generate Implementation Files
```bash
liveapi sync
```
This will generate:
- `implementations/users_service.py` - Service class configured for your chosen backend
- `main.py` - FastAPI application that loads your service
- Database tables (automatically created on first run for SQL backend)

### Step 5: Run Your API
```bash
liveapi run
```

### Step 6: Test Your API
```bash
curl http://localhost:8000/health
# Assuming you created a 'users' API
curl http://localhost:8000/users
```

### Step 7: View Interactive Docs
Open your browser to `http://localhost:8000/docs` to see the Swagger UI.

## Making Changes

### Option 1: Edit Your Spec
1.  **Edit your spec**: Modify your `users.yaml` file to add a new endpoint or change an existing one.
2.  **Check what changed**: Run `liveapi status` to see a summary of your changes.
3.  **Create a new version**: Run `liveapi version create --minor` to create a new, versioned spec file.
4.  **Update your implementation**: Run `liveapi sync` to regenerate service files with changes.

### Option 2: Switch Backend Types
You can change your backend by generating a new API with a different backend option.
1.  **Generate with different backend**: Run `liveapi generate` and choose a different option
2.  **Update configuration**: Backend choice is saved to `.liveapi/config.json`
3.  **Resync implementation**: Run `liveapi sync` to update service files
4.  **Configure new backend**: Set up database URL if switching to SQL

### Option 3: Customize Your Implementation
1.  **Edit service class**: Open `implementations/users_service.py`
2.  **Add business logic**: Implement validation, logging, caching as needed
3.  **Database customization**: For SQL backend, customize queries and relationships
4.  **Test changes**: Your customizations are preserved across spec updates

Example SQL backend customization:
```python
async def create_user(self, user_data: dict) -> dict:
    # Add custom validation
    if not user_data.get("email"):
        raise ValidationError("Email is required")
    
    # Custom database logic (SQL backend handles the connection)
    result = await super().create(user_data)
    
    # Add custom post-processing
    await self.send_welcome_email(result["email"])
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

### Customize Your Implementation
- **Backend Selection**: Choose between in-memory (prototyping) and SQL (production) backends during generation
- **Database Integration**: SQL backend automatically handles PostgreSQL, SQLite connections with proper ORM
- **Business Logic**: Add validation, authorization, logging, caching in service methods
- **Error Handling**: Customize ValidationError and ConflictError responses
- **Custom Endpoints**: Add non-CRUD endpoints alongside generated ones
- **Environment Configuration**: Use DATABASE_URL and DATABASE_DEBUG for SQL backend setup

### Production Deployment
- Your generated service classes are production-ready
- SQL backend provides automatic database connections, pooling, and transaction management
- Database tables are automatically created from your OpenAPI schemas
- Service classes can be version controlled and customized independently
- Environment-based configuration (DATABASE_URL) for different deployment stages
- Use container deployment with your customized implementations

# Database Setup Guide

This guide explains how to configure and use LiveAPI's pluggable database backends.

## Overview

LiveAPI supports two backend options:

1. **DefaultResourceService** - In-memory storage for rapid prototyping
2. **SQLModelResourceService** - SQL database persistence for production

## Backend Selection

### During API Generation

When you run `liveapi generate`, you'll be prompted to choose your backend:

```
Which resource service would you like to use?
1. DefaultResourceService (In-memory, for prototypes)  
2. SQLModelResourceService (PostgreSQL, for production)
Enter choice (1 or 2) [1]:
```

Your choice is automatically saved to `.liveapi/config.json` and used for all future operations.

### Changing Backend Later

You can change backends by regenerating your API with a different choice, or by manually editing `.liveapi/config.json`:

```json
{
  "project_name": "my_api",
  "created_at": "2023-12-01T10:00:00Z",
  "backend_type": "sqlmodel"
}
```

## SQLModel Backend Setup

### 1. Install Dependencies

The SQLModel backend requires additional packages:

```bash
pip install sqlmodel psycopg2-binary
```

- `sqlmodel` - SQLModel ORM for database operations
- `psycopg2-binary` - PostgreSQL adapter (for PostgreSQL databases)

### 2. Database Configuration

Set your database URL using the `DATABASE_URL` environment variable:

#### PostgreSQL (Recommended for Production)
```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
```

#### SQLite (Default for Development)
```bash
export DATABASE_URL="sqlite:///./myapi.db"
```

If no `DATABASE_URL` is set, SQLModel backend defaults to SQLite.

### 3. Database Initialization

LiveAPI automatically:
- Creates database tables on first run
- Handles database connections and sessions
- Manages SQLModel metadata

No manual database setup is required!

### 4. Running with SQL Backend

Once configured, use LiveAPI normally:

```bash
# Generate API with SQLModel backend
liveapi generate
# (Choose option 2 for SQLModelResourceService)

# Sync implementation 
liveapi sync

# Run the API with database persistence
liveapi run
```

## Database Features

### Automatic Table Creation

LiveAPI generates SQLModel tables based on your OpenAPI schema:

```python
# Generated SQLModel class
class User(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    email: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### CRUD Operations

All CRUD operations work transparently with the database:

- **Create**: Automatically generates UUIDs, adds timestamps
- **Read**: Efficient single-record retrieval
- **Update**: Supports both full (PUT) and partial (PATCH) updates
- **Delete**: Safe deletion with proper error handling
- **List**: Supports filtering, pagination, and ordering

### Query Filtering

The SQL backend supports advanced filtering:

```bash
# Exact match
GET /users?name=John

# Comparisons  
GET /users?age__gte=18&age__lte=65

# Text search
GET /users?name__contains=john
```

### Transaction Safety

All operations use proper database transactions:
- Automatic rollback on errors
- Consistent data state
- Proper error handling

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./liveapi.db` |
| `DATABASE_DEBUG` | Enable SQL query logging | `false` |

### Example Environment Setup

```bash
# .env file
DATABASE_URL=postgresql://myuser:mypass@localhost:5432/myapi
DATABASE_DEBUG=true
```

## Production Deployment

### PostgreSQL Setup

1. **Create Database**:
```sql
CREATE DATABASE myapi;
CREATE USER myapi_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE myapi TO myapi_user;
```

2. **Connection String**:
```bash
DATABASE_URL="postgresql://myapi_user:secure_password@localhost:5432/myapi"
```

3. **Deploy**:
```bash
# Set environment variable
export DATABASE_URL="postgresql://myapi_user:secure_password@prod_host:5432/myapi"

# Deploy your API
liveapi run --host 0.0.0.0 --port 8000
```

### Docker Deployment

```dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV DATABASE_URL="postgresql://user:pass@db:5432/myapi"

EXPOSE 8000
CMD ["liveapi", "run", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

**ImportError: No module named 'sqlmodel'**
- Install SQLModel: `pip install sqlmodel`

**Can't connect to PostgreSQL**
- Verify DATABASE_URL format
- Check PostgreSQL is running
- Verify credentials and database exists

**Tables not created**
- Check database permissions
- Verify SQLModel metadata is properly configured
- Check logs for errors

### Debug Mode

Enable SQL query logging:
```bash
export DATABASE_DEBUG=true
liveapi run
```

This will show all SQL queries in the console.

### Performance Optimization

1. **Connection Pooling**: Automatically handled by SQLModel/SQLAlchemy
2. **Indexes**: Add indexes for frequently queried fields
3. **Query Optimization**: Use filtering instead of fetching all records

## Migration from In-Memory

To migrate from DefaultResourceService to SQLModelResourceService:

1. **Backup Data**: Export your current data if needed
2. **Change Backend**: Regenerate API with SQLModel choice
3. **Set Database URL**: Configure your database connection  
4. **Resync**: Run `liveapi sync` to update implementation
5. **Test**: Verify all operations work with database

## Security Considerations

- **Never commit DATABASE_URL** to version control
- **Use environment variables** for credentials
- **Restrict database permissions** to minimum required
- **Use SSL/TLS** for production database connections
- **Regular backups** for production data

## Support

For issues with database integration:
1. Check this documentation
2. Verify environment variables are set correctly
3. Check database connectivity outside of LiveAPI
4. Review error logs with `DATABASE_DEBUG=true`
# automatic

**Runtime OpenAPI to FastAPI. No code generation.**

A Python framework that dynamically creates FastAPI routes from OpenAPI specifications at runtime, eliminating code generation.

## Concept

Instead of:
```
OpenAPI Spec → Generate Code → Implement Business Logic
```

We want:
```
OpenAPI Spec → Runtime Router → Your Implementation Interface
```

Your business logic becomes pure functions:
```python
class ArtObjectImplementation:
    def create_art_object(self, request_data: dict) -> (dict, int):
        # Pure business logic here - no HTTP concerns
        return {"art_object_id": 123}, 201
```

## MVP Requirements

### Core Features
1. **Parse OpenAPI spec** - Load YAML/JSON at startup
2. **Generate FastAPI routes** - Create endpoints from spec
3. **JSON interface** - Pure dict in/out for business logic
4. **Basic validation** - Request validation using spec

### Project Structure
```
automatic/
├── src/
│   └── automatic/
│       ├── __init__.py
│       ├── parser.py     # OpenAPI parsing
│       ├── router.py     # Route generation  
│       └── app.py        # Main interface
├── tests/
├── examples/
├── pyproject.toml
└── README.md
```

## Implementation Plan

### Week 1: Core MVP
1. **OpenAPI Parser** - Parse spec, extract endpoints
2. **Route Generator** - Create FastAPI routes from spec
3. **Basic Interface** - Simple dict in/out

### API Design
```python
import automatic

# Create app
app = automatic.create_app("api.yaml", MyImplementation())

# Implementation
class MyImplementation:
    def create_art_object(self, data):
        return {"id": 1, "title": data["title"]}, 201
```

## Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.9"
fastapi = "^0.100.0"
pydantic = "^2.0.0"
pyyaml = "^6.0"
```

## Success Criteria
- [ ] Load OpenAPI spec and generate working FastAPI app
- [ ] Simple dict interface for business logic  
- [ ] Basic request validation
- [ ] Working example with art objects API

## Installation

```bash
# Install from source
git clone <repository-url>
cd automatic
pip install -e .
```

## Running Tests

The project uses pytest for testing. Run tests with:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run with coverage (if you have pytest-cov installed)
python -m pytest tests/ --cov=src/automatic -v
```

## Usage

### Basic Usage

```python
import automatic

# Create FastAPI app from OpenAPI spec and implementation
app = automatic.create_app("api.yaml", MyImplementation())

# Run with uvicorn
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Implementation Interface

Your implementation class should provide methods that match the `operationId` values in your OpenAPI spec:

```python
class MyImplementation:
    def my_operation(self, data: dict) -> tuple[dict, int]:
        """
        Business logic method.
        
        Args:
            data: Combined request data (body, path params, query params)
            
        Returns:
            tuple: (response_data, status_code)
        """
        return {"result": "success"}, 200
```

## Quick Start

1. **Define your business logic:**
```python
# my_api.py
class ArtObjectsAPI:
    def __init__(self):
        self.art_objects = {}
        self.next_id = 1
    
    def create_art_object(self, data):
        art_object = {
            "id": self.next_id,
            "title": data["title"],
            "artist": data.get("artist", "Unknown")
        }
        self.art_objects[self.next_id] = art_object
        self.next_id += 1
        return art_object, 201
    
    def get_art_object(self, data):
        art_id = int(data["art_object_id"])
        if art_id not in self.art_objects:
            return {"error": "Not found"}, 404
        return self.art_objects[art_id], 200
```

2. **Create your OpenAPI spec:**
```yaml
# api.yaml
openapi: 3.0.0
info:
  title: Art API
  version: 1.0.0
paths:
  /art-objects:
    post:
      operationId: create_art_object
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [title]
              properties:
                title: {type: string}
                artist: {type: string}
      responses:
        201:
          content:
            application/json:
              schema:
                properties:
                  id: {type: integer}
                  title: {type: string}
                  artist: {type: string}
  /art-objects/{art_object_id}:
    get:
      operationId: get_art_object
      parameters:
        - name: art_object_id
          in: path
          required: true
          schema: {type: integer}
      responses:
        200:
          content:
            application/json:
              schema:
                properties:
                  id: {type: integer}
                  title: {type: string}
                  artist: {type: string}
```

3. **Create and run your app:**
```python
import automatic
from my_api import ArtObjectsAPI
import uvicorn

app = automatic.create_app("api.yaml", ArtObjectsAPI())
uvicorn.run(app, port=8000)
```

**That's it. Your API is running at http://localhost:8000**

## Working Example

A complete working example is available in the `examples/` directory:

```bash
# Run the example server
cd examples
python run_example.py
```

This will start a server at http://localhost:8000 with:
- **Interactive docs**: http://localhost:8000/docs 
- **API endpoints**: Based on the OpenAPI spec in `examples/api.yaml`
- **Implementation**: See `examples/my_api.py` for the business logic

### Example API calls:

```bash
# Create an art object
curl -X POST http://localhost:8000/art-objects \
  -H "Content-Type: application/json" \
  -d '{"title": "Mona Lisa", "artist": "Leonardo da Vinci"}'

# Get an art object  
curl http://localhost:8000/art-objects/1
```
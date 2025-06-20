"""Run the Art Objects API example."""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import automatic
from my_api import ArtObjectsAPI
import uvicorn

if __name__ == "__main__":
    # Create the implementation
    api_implementation = ArtObjectsAPI()
    
    # Create the FastAPI app from the OpenAPI spec
    app = automatic.create_app("api.yaml", api_implementation)
    
    print("Starting Art Objects API server...")
    print("API Documentation will be available at: http://localhost:8001/docs")
    print("OpenAPI JSON will be available at: http://localhost:8001/openapi.json")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8001)
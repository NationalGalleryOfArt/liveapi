"""FastAPI application entry point."""

import uvicorn
from automatic import create_app
from test_paintings import PaintingService


def main():
    """Create and run the FastAPI application."""
    # Create the implementation instance
    implementation = PaintingService()
    
    # Create the automatic app
    app = create_app(
        spec_path="specifications/paintings.yaml",
        implementation=implementation
    )
    
    return app


# Create the app instance for deployment
app = main()

if __name__ == "__main__":
    # Run the development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
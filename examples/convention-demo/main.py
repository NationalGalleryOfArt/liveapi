"""Automatic API discovery demo using automatic framework."""

import sys
from pathlib import Path
import automatic
import uvicorn

# Add automatic to path for demo
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def main():
    """Run the automatic API discovery demo."""
    print("🚀 Starting Automatic API Discovery Demo")
    print("📁 API specs: ./api/")
    print("📁 Implementations: ./implementations/")
    print()
    
    # Zero-config mode - automatic discovers files
    app = automatic.create_app()
    
    print("🔍 Discovered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'GET'
            print(f"  {methods:12} {route.path}")
    
    print()
    print("📝 Test the API:")
    print("  curl http://localhost:8000/users")
    print("  curl http://localhost:8000/users/1")
    print("  curl http://localhost:8000/orders")
    print("  curl http://localhost:8000/orders/1")
    print("  curl -X POST http://localhost:8000/users -H 'Content-Type: application/json' -d '{\"name\":\"Charlie\"}'")
    print("  curl -X POST http://localhost:8000/orders -H 'Content-Type: application/json' -d '{\"user_id\":1,\"total\":75.00}'")
    print()
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
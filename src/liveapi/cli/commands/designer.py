"""Designer command for liveapi CLI."""

import sys
import threading
import time
import webbrowser
from pathlib import Path


def cmd_designer(args):
    """Run the LiveAPI Designer server."""
    # Import the designer server module
    designer_dir = Path(__file__).parent.parent.parent.parent.parent / "designer"
    sys.path.insert(0, str(designer_dir))
    
    try:
        import server as designer_server
    except ImportError:
        print("❌ Designer module not found")
        print("   Make sure the 'designer' directory exists in the project root")
        sys.exit(1)
    
    port = args.port
    
    # Function to open browser after a short delay
    def open_browser():
        time.sleep(1.5)  # Wait for server to start
        url = f"http://localhost:{port}/"
        print(f"🌐 Opening browser at {url}")
        webbrowser.open(url)
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the server
    try:
        print(f"🚀 Starting LiveAPI Designer on port {port}")
        designer_server.run_server(port)
    except KeyboardInterrupt:
        print("\n⚠️  Designer server stopped by user")

"""Designer command for liveapi CLI."""

import sys
import threading
import time
import webbrowser
from pathlib import Path

# Import metadata manager for project initialization
from ...metadata_manager import MetadataManager, ProjectStatus


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
    
    # Check if project is initialized
    metadata_manager = MetadataManager()
    status = metadata_manager.get_project_status()
    project_dir = Path.cwd()
    
    # Initialize project if needed
    if status == ProjectStatus.UNINITIALIZED:
        print("📋 Project not initialized. Let's set it up first.")
        project_name = input("Project name (default: directory name): ").strip()
        api_base_url = input("🌐 API base URL (e.g., api.mycompany.com, optional): ").strip()
        
        # Initialize the project
        metadata_manager.initialize_project(
            project_name=project_name or None,
            api_base_url=api_base_url or None
        )
        
        print(f"✨ Project '{project_name or project_dir.name}' initialized successfully!")
        print("📁 Created .liveapi/ directory for metadata")
        if api_base_url:
            print(f"🌐 API base URL configured: {api_base_url}")
    else:
        config = metadata_manager.load_config()
        print(f"📁 Using existing project: {config.project_name}")
    
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
    
    # Start the server with project directory
    try:
        print(f"🚀 Starting LiveAPI Designer on port {port}")
        designer_server.run_server(port, project_dir)
    except KeyboardInterrupt:
        print("\n⚠️  Designer server stopped by user")

#!/usr/bin/env python3
"""
Simple server for LiveAPI Designer
Serves static files and handles API generation requests
"""
import json
import os
import sys
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path modification
try:
    from src.liveapi.spec_generator import SpecGenerator
except ImportError:
    print("Error: Could not import SpecGenerator. Make sure the liveapi package is installed.")
    sys.exit(1)


class DesignerHandler(SimpleHTTPRequestHandler):
    # Cache for the generated OpenAPI spec
    _cached_openapi_spec = None
    def do_GET(self):
        """Handle GET requests with root redirect"""
        if self.path == '/' or self.path == '':
            # Redirect to designer.html
            self.send_response(302)
            self.send_header('Location', '/designer.html')
            self.end_headers()
            return
        elif self.path == '/api/resources':
            # List all resources in the project
            if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                resources = []
                
                # Check .liveapi/prompts for saved schemas
                prompts_dir = self.__class__.project_dir / '.liveapi' / 'prompts'
                if prompts_dir.exists():
                    for schema_file in prompts_dir.glob('*_schema.json'):
                        try:
                            with open(schema_file, 'r') as f:
                                schema_data = json.load(f)
                                # Extract resource info
                                resource_name = schema_file.stem.replace('_schema', '')
                                resources.append({
                                    'name': resource_name,
                                    'api_name': schema_data.get('api_name', 'Unknown API'),
                                    'description': schema_data.get('api_description', ''),
                                    'file': str(schema_file.relative_to(self.__class__.project_dir))
                                })
                        except Exception as e:
                            print(f"Error reading {schema_file}: {e}")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(resources).encode())
                return
            
            # No project directory
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps([]).encode())
            return
        elif self.path.startswith('/api/resource/'):
            # Load a specific resource
            resource_name = self.path.split('/')[-1]
            if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                schema_file = self.__class__.project_dir / '.liveapi' / 'prompts' / f"{resource_name}_schema.json"
                if schema_file.exists():
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    with open(schema_file, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            
            # Resource not found
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Resource not found'}).encode())
            return
        elif self.path == '/api/config':
            # Get project configuration
            if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                config_file = self.__class__.project_dir / '.liveapi' / 'config.json'
                if config_file.exists():
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    with open(config_file, 'rb') as f:
                        self.wfile.write(f.read())
                    return
            
            # Default config
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'project_name': 'My API Project',
                'api_base_url': ''
            }).encode())
            return
        elif self.path == '/api/openapi.json' or self.path.startswith('/api/openapi.json?'):
            # Serve openapi.json - try cache first, then file
            # First try to serve from cache
            if hasattr(self.__class__, '_cached_openapi_spec') and self.__class__._cached_openapi_spec:
                print(f"✅ [Server] Serving OpenAPI spec from cache")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(self.__class__._cached_openapi_spec).encode())
                return
            
            # Then try to serve from file
            print(f"🔍 [Server] No cache, trying file...")
            print(f"🔍 [Server] Has project_dir: {hasattr(self.__class__, 'project_dir')}")
            if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                print(f"🔍 [Server] Project dir: {self.__class__.project_dir}")
                openapi_file = self.__class__.project_dir / '.liveapi' / 'openapi.json'
                print(f"🔍 [Server] Looking for file: {openapi_file}")
                print(f"🔍 [Server] File exists: {openapi_file.exists()}")
                
                if openapi_file.exists():
                    print(f"✅ [Server] Serving openapi.json from file: {openapi_file}")
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    with open(openapi_file, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                else:
                    # Debug file system
                    liveapi_dir = self.__class__.project_dir / '.liveapi'
                    print(f"🔍 [Server] .liveapi dir exists: {liveapi_dir.exists()}")
                    if liveapi_dir.exists():
                        print(f"🔍 [Server] .liveapi contents: {list(liveapi_dir.iterdir())}")
            else:
                print(f"❌ [Server] No project_dir set")
                
            # File not found
            print(f"❌ [Server] OpenAPI spec not found, returning 404")
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'OpenAPI spec not found'}).encode())
            return
        return super().do_GET()
        
    def do_DELETE(self):
        """Handle DELETE requests"""
        if self.path.startswith('/api/resource/'):
            # Delete a resource
            resource_name = self.path.split('/')[-1]
            if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                # Delete schema file
                schema_file = self.__class__.project_dir / '.liveapi' / 'prompts' / f"{resource_name}_schema.json"
                prompt_file = self.__class__.project_dir / '.liveapi' / 'prompts' / f"{resource_name}_prompt.json"
                spec_file = self.__class__.project_dir / 'specifications' / f"{resource_name}.json"
                
                deleted = False
                if schema_file.exists():
                    schema_file.unlink()
                    deleted = True
                if prompt_file.exists():
                    prompt_file.unlink()
                    deleted = True
                if spec_file.exists():
                    spec_file.unlink()
                    deleted = True
                
                if deleted:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True}).encode())
                    return
            
            # Resource not found
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Resource not found'}).encode())
            return
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for API generation"""
        if self.path == '/api/config':
            # Update project configuration
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                config_data = json.loads(post_data)
                
                if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                    config_file = self.__class__.project_dir / '.liveapi' / 'config.json'
                    
                    # Read existing config
                    existing_config = {}
                    if config_file.exists():
                        with open(config_file, 'r') as f:
                            existing_config = json.load(f)
                    
                    # Update with new values
                    existing_config.update(config_data)
                    
                    # Save back
                    with open(config_file, 'w') as f:
                        json.dump(existing_config, f, indent=2)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True}).encode())
                    return
                
                # No project directory
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Project directory not set'}).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
                
        elif self.path == '/sync':
            try:
                # Check if project directory is set
                if not hasattr(self.__class__, 'project_dir') or not self.__class__.project_dir:
                    raise ValueError("Project directory not set. Please restart the designer.")
                
                # Run liveapi sync command
                print(f"🔄 Running liveapi sync in {self.__class__.project_dir}")
                result = subprocess.run(
                    ["liveapi", "sync"],
                    cwd=self.__class__.project_dir,
                    capture_output=True,
                    text=True
                )
                
                # Check if command was successful
                if result.returncode == 0:
                    print("✅ Sync completed successfully")
                    success_message = "Implementation files generated successfully"
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'message': success_message,
                        'output': result.stdout
                    }).encode())
                else:
                    print(f"❌ Sync failed: {result.stderr}")
                    # Send error response
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': f"Sync failed: {result.stderr}"
                    }).encode())
                    
            except Exception as e:
                # Send error response
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': str(e)
                }).encode())
                
        elif self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # Parse the JSON data
                api_info = json.loads(post_data)
                
                # Transform api_info to match generator expectations
                if 'objects' in api_info and api_info['objects']:
                    first_object = api_info['objects'][0]
                    transformed_info = {
                        'name': api_info.get('api_name', 'API'),
                        'description': api_info.get('api_description', ''),
                        'resource_name': first_object['name'],
                        'resource_description': first_object.get('description', ''),
                        'resource_schema': first_object.get('fields', {}),
                        'examples': [first_object.get('example', {})] if 'example' in first_object else [],
                        'resource_type': api_info.get('x-resource-type', 'DefaultResourceService')
                    }
                else:
                    transformed_info = api_info
                
                # Generate the spec
                generator = SpecGenerator()
                spec_dict, _ = generator.generate_spec_with_json(transformed_info)
                print(f"✅ [Server] Generated OpenAPI spec: {spec_dict.get('info', {}).get('title')}")
                
                # Cache the spec for immediate serving
                self.__class__._cached_openapi_spec = spec_dict
                
                # Save to project .liveapi directory if available
                if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                    # Save the working openapi.json to .liveapi directory
                    liveapi_dir = self.__class__.project_dir / '.liveapi'
                    liveapi_dir.mkdir(exist_ok=True)
                    working_file = liveapi_dir / 'openapi.json'
                    
                    with open(working_file, 'w') as f:
                        json.dump(spec_dict, f, indent=2)
                        f.flush()  # Ensure data is written to disk
                        os.fsync(f.fileno())  # Force write to disk
                    
                    print(f"✅ [Server] Saved to: {working_file}")
                else:
                    print(f"❌ [Server] No project_dir available for saving openapi.json")
                
                # Also save to project specifications directory if available
                if hasattr(self.__class__, 'project_dir') and self.__class__.project_dir:
                    # Create specifications directory if it doesn't exist
                    project_specs_dir = self.__class__.project_dir / 'specifications'
                    project_specs_dir.mkdir(exist_ok=True)
                    
                    # Use resource name for the filename
                    resource_name = transformed_info.get('resource_name', 'api')
                    project_spec_file = project_specs_dir / f"{resource_name}.json"
                    
                    # Save the spec to the project
                    with open(project_spec_file, 'w') as f:
                        json.dump(spec_dict, f, indent=2)
                    
                    print(f"✅ OpenAPI specification saved to project: {project_spec_file}")
                    
                    # Also save the design JSON to .liveapi/prompts
                    prompts_dir = self.__class__.project_dir / '.liveapi' / 'prompts'
                    prompts_dir.mkdir(exist_ok=True)
                    
                    prompt_file = prompts_dir / f"{resource_name}_schema.json"
                    with open(prompt_file, 'w') as f:
                        json.dump(api_info, f, indent=2)
                    
                    print(f"✅ Design JSON saved to: {prompt_file}")
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': 'OpenAPI spec generated successfully'
                }).encode())
                
            except Exception as e:
                # Send error response
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': str(e)
                }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def end_headers(self):
        """Add CORS headers to allow requests from the browser"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()


def run_server(port=8888, project_dir=None):
    """Run the designer server"""
    # Change to the directory where server.py is located
    os.chdir(Path(__file__).parent)
    
    # Store project directory for use by the handler
    if project_dir:
        DesignerHandler.project_dir = Path(project_dir)
    else:
        DesignerHandler.project_dir = None
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DesignerHandler)
    print(f"LiveAPI Designer Server running on http://localhost:{port}")
    print(f"Open http://localhost:{port}/designer.html in your browser")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    run_server(port)

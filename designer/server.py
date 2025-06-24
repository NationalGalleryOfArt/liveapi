#!/usr/bin/env python3
"""
Simple server for LiveAPI Designer
Serves static files and handles API generation requests
"""
import json
import os
import sys
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
    def do_GET(self):
        """Handle GET requests with root redirect"""
        if self.path == '/' or self.path == '':
            # Redirect to designer.html
            self.send_response(302)
            self.send_header('Location', '/designer.html')
            self.end_headers()
            return
        return super().do_GET()
        
    def do_POST(self):
        """Handle POST requests for API generation"""
        if self.path == '/generate':
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
                        'examples': [first_object.get('example', {})] if 'example' in first_object else []
                    }
                else:
                    transformed_info = api_info
                
                # Generate the spec
                generator = SpecGenerator()
                spec_dict, _ = generator.generate_spec_with_json(transformed_info)
                
                # Save to build directory
                output_dir = Path(__file__).parent / 'build'
                output_dir.mkdir(exist_ok=True)
                output_file = output_dir / 'openapi.json'
                
                with open(output_file, 'w') as f:
                    json.dump(spec_dict, f, indent=2)
                
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


def run_server(port=8888):
    """Run the designer server"""
    # Change to the directory where server.py is located
    os.chdir(Path(__file__).parent)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, DesignerHandler)
    print(f"LiveAPI Designer Server running on http://localhost:{port}")
    print(f"Open http://localhost:{port}/designer.html in your browser")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    run_server(port)

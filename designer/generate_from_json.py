#!/usr/bin/env python3
"""
Bridge script that generates OpenAPI spec from JSON design file.
Usage: python generate_from_json.py my_api_design.json
"""
import sys
import json
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.liveapi.spec_generator import SpecGenerator


def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python generate_from_json.py <json_file>")
        print("Example: python generate_from_json.py my_api.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found")
        sys.exit(1)
    
    # Load and parse JSON
    try:
        with open(json_file, 'r') as f:
            api_info = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{json_file}'")
        print(f"Details: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {str(e)}")
        sys.exit(1)
    
    # Validate required fields
    required_fields = ['api_name', 'api_description', 'objects']
    missing_fields = [field for field in required_fields if field not in api_info]
    if missing_fields:
        print(f"Error: Missing required fields: {', '.join(missing_fields)}")
        print("Required structure:")
        print(json.dumps({
            "api_name": "string",
            "api_description": "string", 
            "objects": [
                {
                    "name": "string",
                    "description": "string",
                    "fields": {"field_name": "field_type"},
                    "example": {"field_name": "value"}
                }
            ]
        }, indent=2))
        sys.exit(1)
    
    # Initialize generator
    try:
        generator = SpecGenerator()
    except Exception as e:
        print(f"Error initializing generator: {str(e)}")
        sys.exit(1)
    
    # Transform api_info to match generator expectations
    if 'objects' in api_info and api_info['objects']:
        # Use the first object as the main resource
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
    
    # Generate specification
    print(f"Generating OpenAPI spec for '{api_info['api_name']}'...")
    try:
        spec_dict, intermediate_json = generator.generate_spec_with_json(transformed_info)
    except Exception as e:
        print(f"Error generating specification: {str(e)}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent / 'build'
    output_dir.mkdir(exist_ok=True)
    
    # Save the specification
    output_file = output_dir / 'openapi.json'
    try:
        with open(output_file, 'w') as f:
            json.dump(spec_dict, f, indent=2)
        print(f"✓ OpenAPI specification saved to: {output_file}")
        print("✓ Open designer/preview.html in your browser to view the documentation")
    except Exception as e:
        print(f"Error saving specification: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
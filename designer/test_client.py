#!/usr/bin/env python3
"""
Test client for the LiveAPI Designer server
Makes a request to the server to generate an OpenAPI spec
"""
import json
import requests
from pathlib import Path

# Test data
test_data = {
    "api_name": "Test API",
    "api_description": "A test API for verifying the server",
    "objects": [
        {
            "name": "tests",
            "description": "Test objects",
            "fields": {
                "name": "string",
                "status": "string",
                "priority": "integer"
            },
            "example": {
                "name": "Test Case 1",
                "status": "passed",
                "priority": 1
            }
        }
    ]
}

def test_generate_api():
    """Test the /generate endpoint"""
    print("Testing API generation...")
    try:
        response = requests.post(
            "http://localhost:8888/generate",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Success! API generated successfully")
                
                # Check if the file was created
                output_file = Path(__file__).parent / "build" / "openapi.json"
                if output_file.exists():
                    print(f"✅ OpenAPI spec saved to: {output_file}")
                    
                    # Verify the content
                    with open(output_file, "r") as f:
                        spec = json.load(f)
                    
                    if spec.get("info", {}).get("title") == "Test API":
                        print("✅ Generated spec has correct title")
                    else:
                        print("❌ Generated spec has incorrect title")
                        
                    if "/tests" in spec.get("paths", {}):
                        print("✅ Generated spec has correct endpoints")
                    else:
                        print("❌ Generated spec is missing endpoints")
                else:
                    print(f"❌ OpenAPI spec file not found at: {output_file}")
            else:
                print(f"❌ Error: {result.get('error')}")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on port 8888")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_generate_api()

#!/usr/bin/env python3
"""Example of using LiveAPI to generate OpenAPI specifications with AI."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from liveapi.spec_generator import SpecGenerator, check_api_key


def main():
    """Demonstrate spec generation."""
    
    # Ensure API key is available (will prompt if needed)
    try:
        from liveapi.spec_generator import ensure_api_key
        ensure_api_key()
    except (KeyboardInterrupt, ValueError):
        print("Cannot proceed without API key")
        return
    
    # Example 1: Generate spec programmatically
    print("Example 1: Programmatic generation")
    print("-" * 40)
    
    generator = SpecGenerator()
    
    # Using the new format with SQL-like attribute definitions
    api_info = {
        "name": "Art Gallery API",
        "description": "Art locations for an art gallery",
        "endpoint_descriptions": """/locations - returns all locations - locations contain:
[locationID] [int] NOT NULL,
[site] [nvarchar](64) NULL,
[room] [nvarchar](64) NULL,
[active] [int] NOT NULL,
[description] [nvarchar](256) NULL,
[unitPosition] [nvarchar](64) NULL

/locations/{id} - returns a specific location by ID

/locations - POST creates a new location

/locations/{id} - PUT updates a location

/locations/{id} - DELETE removes a location"""
    }
    
    print("Generating spec for:", api_info["description"])
    print("\nFeatures:")
    print("- API Key authentication (X-API-Key header)")
    print("- RFC9457 problem details for errors")
    print("- Comprehensive error handling (200, 201, 204, 400, 401, 404, 500, 503)")
    print("- <200ms response time SLA")
    
    try:
        spec = generator.generate_spec(api_info)
        saved_path = generator.save_spec(spec, "art_gallery_api.yaml")
        print(f"\n✅ Spec saved to: {saved_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print()
    
    # Example 2: Interactive generation
    print("Example 2: Interactive generation")
    print("-" * 40)
    print("Try running: liveapi generate")
    print("Or just: liveapi (for full interactive experience)")


if __name__ == "__main__":
    main()
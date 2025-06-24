"""Spec generation commands for liveapi CLI."""

import sys
from pathlib import Path

from ...metadata_manager import MetadataManager, ProjectStatus
from ...change_detector import ChangeDetector
from ...spec_generator import SpecGenerator


def cmd_generate(args):
    """Generate OpenAPI specification."""
    try:
        # Initialize generator
        generator = SpecGenerator()

        # Generate interactively
        spec = generator.interactive_generate()

        # Determine output path
        output_path = args.output
        if not output_path:
            # Generate default name based on API name
            api_name = spec.get("info", {}).get("title", "generated_api")
            # Convert to filename format
            import re

            filename = re.sub(r"[^a-zA-Z0-9]+", "_", api_name.lower()).strip("_")

            # Ensure specifications directory exists and save there by default
            specs_dir = Path.cwd() / "specifications"
            specs_dir.mkdir(exist_ok=True)
            file_ext = args.format
            output_path = specs_dir / (filename + "." + file_ext)

        # Save the spec
        saved_path = generator.save_spec(spec, output_path, args.format)
        print(f"\n✅ Specification saved to: {saved_path}")

        # If in an initialized project, track the new spec
        metadata_manager = MetadataManager()
        if metadata_manager.get_project_status() != ProjectStatus.UNINITIALIZED:
            change_detector = ChangeDetector()
            change_detector.update_spec_tracking(Path(saved_path))
            print("📋 Specification tracked in project")
            print("\n🎯 Next steps:")
            print(f"  1. Review the generated spec: {saved_path}")
            print("  2. Or edit the schema JSON for quick API changes")
            print("  3. Run 'liveapi sync' to generate implementation")
            print("  4. Run 'liveapi run' to test out the API")

            # Generate a sample curl command based on the first endpoint
            try:
                if spec and "paths" in spec:
                    first_path = next(iter(spec["paths"].keys()))
                    first_method = next(iter(spec["paths"][first_path].keys())).upper()

                    # Get server URL (prefer localhost for testing)
                    server_url = "http://localhost:8000"
                    if "servers" in spec and spec["servers"]:
                        for server in spec["servers"]:
                            if "localhost" in server.get("url", ""):
                                server_url = server["url"]
                                break

                    curl_url = f"{server_url}{first_path}"
                    if first_method == "GET":
                        print(f"  5. Test with: curl {curl_url}")
                    else:
                        print(f"  5. Test with: curl -X {first_method} {curl_url}")
                else:
                    print("  5. Test with curl commands once the server is running")
            except Exception:
                print("  5. Test with curl commands once the server is running")

            print("  6. Run 'liveapi version create' when ready to version")

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        sys.exit(1)

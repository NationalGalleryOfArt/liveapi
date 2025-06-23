"""Interactive workflow for OpenAPI spec generation."""

import json
import datetime
import re
from typing import Dict, Any, Optional
from pathlib import Path


class InteractiveGenerator:
    """Handles interactive generation of OpenAPI specifications."""

    def __init__(self, spec_generator):
        """Initialize with a SpecGenerator instance.

        Args:
            spec_generator: SpecGenerator instance to use for generation
        """
        self.spec_generator = spec_generator

    def collect_api_info(
        self, existing_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Collect API information from user input.

        Args:
            existing_info: Optional existing API info to use as defaults

        Returns:
            Dictionary with API information
        """
        # Always generate CRUD API - ask for object name first
        print("What is the object name? (e.g., users, products, locations)")
        if existing_info and "resource_name" in existing_info:
            print(f"Current: {existing_info['resource_name']}")
        resource_name = input("> ").strip().lower()
        if not resource_name and existing_info and "resource_name" in existing_info:
            resource_name = existing_info["resource_name"]
        elif not resource_name:
            resource_name = "items"

        # Get object description
        print(f"\nDescribe the {resource_name} object:")
        if existing_info and "resource_description" in existing_info:
            print(f"Current: {existing_info['resource_description']}")
        resource_description = input("> ").strip()
        if not resource_description and existing_info and "resource_description" in existing_info:
            resource_description = existing_info["resource_description"]
        elif not resource_description:
            resource_description = f"A {resource_name} resource"

        # Auto-infer API name from resource name (capitalize and add 'API')
        default_api_name = f"{resource_name.capitalize()} API"
        
        # Get API name (with smart default)
        print(f"\nAPI name (default: {default_api_name}):")
        if existing_info and "name" in existing_info:
            print(f"Current: {existing_info['name']}")
        name = input("> ").strip()
        if not name and existing_info and "name" in existing_info:
            name = existing_info["name"]
        elif not name:
            name = default_api_name

        # Auto-infer API description from resource description
        default_description = resource_description
        
        # Get API description (with smart default)
        print(f"\nAPI description (default: {default_description}):")
        if existing_info and "description" in existing_info:
            print(f"Current: {existing_info['description']}")
        description = input("> ").strip()
        if not description and existing_info and "description" in existing_info:
            description = existing_info["description"]
        elif not description:
            description = default_description

        # Auto-infer project name from resource name (no need to ask again)
        project_name = re.sub(r"[^a-zA-Z0-9]+", "_", resource_name.lower()).strip("_")
        if existing_info and "project_name" in existing_info:
            project_name = existing_info["project_name"]
        
        # Try to get base URL from existing project config first
        base_url = "https://api.example.com"  # default fallback
        if existing_info and "base_url" in existing_info:
            base_url = existing_info["base_url"]
        else:
            # Check if we're in an initialized project and get base URL from config
            try:
                from ..metadata_manager import MetadataManager
                metadata_manager = MetadataManager()
                config = metadata_manager.load_config()
                if config.api_base_url:
                    base_url = f"https://{config.api_base_url}"
            except Exception:
                pass  # Use default if config not available

        # Ask for JSON schema
        print(
            f"\nPaste the JSON attributes for {resource_name} (press Enter twice when done):"
        )
        print("Example format:")
        print(
            """  {
    "name": "string",
    "email": "string", 
    "age": "integer",
    "active": "boolean"
  }"""
        )
        schema_lines = []
        empty_count = 0

        while empty_count < 2:
            line = input()
            if not line:
                empty_count += 1
            else:
                empty_count = 0
                schema_lines.append(line)

        schema_json = "\n".join(schema_lines).strip()

        # Try to parse the JSON schema
        schema_was_valid = True
        try:
            resource_schema = json.loads(schema_json)
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON. Using a default schema.")
            resource_schema = {"name": "string", "description": "string"}
            schema_was_valid = False

        # Ask for examples as a JSON array
        print(f"\nProvide 2-3 example {resource_name} records as a JSON array:")
        print("Example format:")
        print("[")
        print("  {\"name\": \"Example 1\", \"description\": \"First example\"},")
        print("  {\"name\": \"Example 2\", \"description\": \"Second example\"}")
        print("]")
        print("\nPaste your JSON array (press Enter twice when done):")
        
        example_lines = []
        empty_count = 0

        while empty_count < 2:
            line = input()
            if not line:
                empty_count += 1
            else:
                empty_count = 0
                example_lines.append(line)

        examples_json = "\n".join(example_lines).strip()
        
        try:
            examples = json.loads(examples_json)
            if not isinstance(examples, list):
                print("⚠️ Expected a JSON array. Using default examples.")
                examples = []
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON. Using default examples.")
            examples = []

        if not examples:
            # Create default examples based on schema
            if "name" in resource_schema:
                examples = [
                    {"name": f"Example {resource_name} 1"},
                    {"name": f"Example {resource_name} 2"}
                ]
            else:
                examples = [{}, {}]
        
        # Merge fields from examples into schema to ensure consistency
        # Only do this if the user provided a valid schema (not the default fallback)
        if examples and schema_was_valid:
            # First pass: add missing fields from examples to schema
            for example in examples:
                for field_name, field_value in example.items():
                    if field_name not in resource_schema:
                        # Infer type from the example value
                        if isinstance(field_value, int):
                            resource_schema[field_name] = "integer"
                        elif isinstance(field_value, bool):
                            resource_schema[field_name] = "boolean"
                        elif isinstance(field_value, float):
                            resource_schema[field_name] = "number"
                        else:
                            resource_schema[field_name] = "string"
                        print(f"📝 Added field '{field_name}' ({resource_schema[field_name]}) from examples")
            
        # Always normalize examples to use 'id' instead of resource-specific id fields
        if examples:
            normalized_examples = []
            for example in examples:
                normalized_example = {}
                for field_name, field_value in example.items():
                    # Convert resource_id variations to 'id'
                    if field_name.endswith('_id') and field_name == f"{resource_name[:-1]}_id":
                        normalized_example['id'] = field_value
                        print(f"🔄 Normalized '{field_name}' to 'id' in examples")
                    else:
                        normalized_example[field_name] = field_value
                normalized_examples.append(normalized_example)
            examples = normalized_examples

        return {
            "name": name,
            "description": description,
            "project_name": project_name,
            "base_url": base_url,
            "is_crud": True,
            "resource_name": resource_name,
            "resource_description": resource_description,
            "resource_schema": resource_schema,
            "examples": examples,
        }

    def save_prompt_and_json(
        self, api_info: Dict[str, Any], spec: Dict[str, Any], llm_json: Dict[str, Any]
    ) -> None:
        """Save prompt data and intermediate JSON for future regeneration.

        Args:
            api_info: API information dictionary
            spec: Generated OpenAPI spec
            llm_json: Intermediate LLM JSON response
        """
        # Create prompts directory in the project root (where .liveapi exists)
        from ..metadata_manager import MetadataManager

        metadata_manager = MetadataManager()
        project_root = metadata_manager.project_root
        prompts_dir = project_root / ".liveapi" / "prompts"
        prompts_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename based on project_name if available, otherwise API name
        name_for_filename = api_info.get("project_name", api_info["name"])
        filename = re.sub(r"[^a-zA-Z0-9]+", "_", name_for_filename.lower()).strip("_")
        prompt_file = prompts_dir / f"{filename}_prompt.json"
        json_file = prompts_dir / f"{filename}_schema.json"

        # Add metadata
        prompt_data = {
            "api_info": api_info,
            "metadata": {
                "created_at": datetime.datetime.now().isoformat(),
                "model": self.spec_generator.model,
                "generated_spec_title": spec.get("info", {}).get("title", "Unknown"),
                "generated_spec_version": spec.get("info", {}).get("version", "1.0.0"),
            },
        }

        with open(prompt_file, "w") as f:
            json.dump(prompt_data, f, indent=2)

        # Save the intermediate JSON schema
        with open(json_file, "w") as f:
            json.dump(llm_json, f, indent=2)

        print(f"💾 Prompt saved to: {prompt_file.absolute()}")
        print(f"📋 Schema saved to: {json_file.absolute()}")
        print("   Edit the schema JSON to modify endpoints/objects, then:")
        print(f"   liveapi regenerate {prompt_file.absolute()}")

    def load_prompt(self, prompt_file: str) -> Dict[str, Any]:
        """Load saved prompt data.

        Args:
            prompt_file: Path to the prompt file

        Returns:
            API information dictionary
        """
        with open(prompt_file, "r") as f:
            prompt_data = json.load(f)

        return prompt_data["api_info"]

    def get_schema_file_from_prompt(self, prompt_file: str) -> Optional[Path]:
        """Get the corresponding schema file for a prompt file.

        Args:
            prompt_file: Path to the prompt file

        Returns:
            Path to the schema file if it exists
        """
        prompt_path = Path(prompt_file)
        # Replace _prompt.json with _schema.json
        schema_name = prompt_path.name.replace("_prompt.json", "_schema.json")
        return prompt_path.parent / schema_name

    def schema_modified_since_prompt(self, prompt_file: str, schema_file: Path) -> bool:
        """Check if schema file has been modified since the prompt was created.

        Args:
            prompt_file: Path to the prompt file
            schema_file: Path to the schema file

        Returns:
            True if schema file is newer than prompt file
        """
        try:
            prompt_stat = Path(prompt_file).stat()
            schema_stat = schema_file.stat()
            # If schema is newer than prompt, it was likely manually edited
            return schema_stat.st_mtime > prompt_stat.st_mtime
        except (OSError, AttributeError):
            return False

    def interactive_generate(self, prompt_file: Optional[str] = None) -> Dict[str, Any]:
        """Interactively prompt user for API details and generate spec.

        Args:
            prompt_file: Optional path to a saved prompt file

        Returns:
            Generated OpenAPI specification
        """
        print("\n🚀 Welcome to LiveAPI CRUD Generator!")
        print("I'll help you create a CRUD+ API with:")
        print("  • Full CRUD operations (Create, Read, Update, Delete, List)")
        print("  • Search and filtering")
        print("  • API key authentication")
        print("  • RFC9457 error handling")
        print("  • <200ms response time SLA\n")

        # No longer need API key validation

        # Load existing prompt if provided
        if prompt_file and Path(prompt_file).exists():
            print(f"📂 Loading saved prompt from: {prompt_file}")
            api_info = self.load_prompt(prompt_file)
            print(f"   API Name: {api_info['name']}")
            print(f"   Description: {api_info['description']}")

            # Handle both old and new format
            if "endpoint_descriptions" in api_info:
                print(
                    f"   Endpoints: {len(api_info['endpoint_descriptions'].splitlines())} lines"
                )
            elif "is_crud" in api_info and api_info["is_crud"]:
                print(f"   Resource: {api_info['resource_name']}")
                print(f"   Schema Fields: {len(api_info['resource_schema'])} fields")

            # Check if there's a corresponding schema file
            schema_file = self.get_schema_file_from_prompt(prompt_file)
            if schema_file and schema_file.exists():
                print(f"📋 Schema file found: {schema_file}")
                print("   You can edit the schema JSON to modify endpoints/objects")
                print()

                # Check if schema has been modified since prompt was created
                if self.schema_modified_since_prompt(prompt_file, schema_file):
                    print("🔧 Schema has been modified - using edited schema")
                    # Generate spec directly from the modified schema
                    with open(schema_file) as f:
                        llm_json = json.load(f)
                    spec = self.spec_generator._build_spec_from_structured_data(
                        llm_json, api_info["name"], api_info["description"]
                    )
                    return self.spec_generator._add_server_environments(spec)

            print()
            # Ask if user wants to use saved prompt or edit it
            choice = input("Use saved prompt (y) or edit it (n)? [y]: ").strip().lower()
            if choice in ["n", "no"]:
                api_info = self.collect_api_info(api_info)
        else:
            # Collect new API info
            api_info = self.collect_api_info()

        print("\n✨ Generating your OpenAPI specification...")
        print(f"Using model: {self.spec_generator.model}")
        print("Features: RFC9457 errors, <200ms response time SLA")

        # Generate the spec
        spec, llm_json = self.spec_generator.generate_spec_with_json(api_info)

        # Save both the prompt and intermediate JSON for future regeneration
        self.save_prompt_and_json(api_info, spec, llm_json)

        return spec

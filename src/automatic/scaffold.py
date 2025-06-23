"""Scaffold generation for automatic implementations."""

import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
from .parser import OpenAPIParser
from .typegen import TypedDictGenerator


class ScaffoldGenerator:
    """Generates implementation scaffolds from OpenAPI specifications using Jinja templates."""

    def __init__(self, spec_path: str):
        self.spec_path = Path(spec_path)
        self.parser = OpenAPIParser(spec_path)

        # Set up Jinja environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True
        )

        # Add custom filters
        self.jinja_env.filters["to_snake_case"] = self._to_snake_case

    def get_default_output_path(self) -> str:
        """Generate default output path in implementations/ directory."""
        # Parse routes to get class name
        routes = self.parser.get_routes()
        template_data = self._prepare_template_data(routes)
        class_name = template_data["class_name"]

        # Convert class name to snake_case filename
        # UserService -> user_service.py
        # UsersV2Service -> users_v2_service.py
        filename = self._class_name_to_filename(class_name)

        # Create implementations directory if it doesn't exist
        implementations_dir = Path("implementations")
        implementations_dir.mkdir(exist_ok=True)

        return str(implementations_dir / filename)

    def _class_name_to_filename(self, class_name: str) -> str:
        """Convert class name to snake_case filename."""
        # Remove 'Service' suffix if present
        if class_name.endswith("Service"):
            base_name = class_name[:-7]  # Remove 'Service'
        else:
            base_name = class_name

        # Convert PascalCase to snake_case
        # UserV2 -> user_v2
        import re

        snake_case = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", base_name).lower()

        return f"{snake_case}_service.py"

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case for use in Jinja templates."""
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    def generate_scaffold(self, output_path: str) -> bool:
        """Generate scaffold implementation file and optionally initialize project.

        Returns:
            bool: True if successful, False if cancelled by user
        """
        output_file = Path(output_path)

        # Auto-detect if this should be a project initialization
        should_init = self._should_init_project()

        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if implementation file exists and ask user
        if output_file.exists():
            response = input(
                f"⚠️  File '{output_path}' already exists. Overwrite? (y/N): "
            )
            if response.lower() not in ["y", "yes"]:
                print("❌ Scaffold generation cancelled.")
                return False

        # Check if we're initializing and main.py exists, ask user
        if should_init and Path("main.py").exists():
            response = input("⚠️  main.py already exists. Overwrite? (y/N): ")
            if response.lower() not in ["y", "yes"]:
                print("❌ Project initialization cancelled.")
                should_init = False

        # Parse the OpenAPI spec and prepare template data
        routes = self.parser.get_routes()
        template_data = self._prepare_template_data(routes)

        # Generate TypedDict definitions
        typegen = TypedDictGenerator()
        type_definitions = typegen.generate_types_for_routes(routes)
        template_data["type_definitions"] = type_definitions

        # Choose template based on API type
        template_name = (
            "crud_implementation.py.j2"
            if template_data["use_crud_base"]
            else "standard_implementation.py.j2"
        )
        template = self.jinja_env.get_template(template_name)

        # Generate code from template
        code = template.render(**template_data)

        # Write to file
        output_file.write_text(code)

        # Initialize project structure if needed
        if should_init:
            self._init_project_structure(output_file, template_data)

        return True

    def _prepare_template_data(self, routes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data for template rendering."""
        # Determine if this looks like a CRUD API
        use_crud_base, resource_name = self._analyze_crud_patterns(routes)

        # Extract schema information from the OpenAPI spec
        schema_info = self._extract_schema_info()

        # Process routes for template
        processed_routes = []
        for route in routes:
            processed_route = {
                "operation_id": route["operation_id"],
                "method": route["method"],
                "path": route["path"],
                "summary": route.get("summary", ""),
                "description": route.get("description", ""),
                "success_codes": [
                    code
                    for code in route.get("responses", {}).keys()
                    if code.startswith("2")
                ],
                "error_codes": [
                    code
                    for code in route.get("responses", {}).keys()
                    if not code.startswith("2")
                ],
                "request_body": route.get("request_body", {}),
            }

            # Add CRUD mapping for CRUD APIs
            if use_crud_base:
                processed_route["crud_mapping"] = self._map_to_crud_operation(
                    route["operation_id"], route["method"], route["path"]
                )

            processed_routes.append(processed_route)

        return {
            "class_name": self._get_class_name(resource_name),
            "resource_name": resource_name,
            "use_crud_base": use_crud_base,
            "routes": processed_routes,
            "schema_info": schema_info,
        }

    def _extract_schema_info(self) -> Dict[str, Any]:
        """Extract schema information from the OpenAPI spec."""
        # Load the spec if not already loaded
        if not hasattr(self.parser, "spec") or self.parser.spec is None:
            self.parser.load_spec()

        # Extract schemas from components
        schemas = self.parser.spec.get("components", {}).get("schemas", {})

        # Process each schema to extract properties and required fields
        schema_info = {}
        for schema_name, schema in schemas.items():
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            schema_info[schema_name] = {
                "properties": properties,
                "required": required,
            }

        return schema_info

    def _analyze_crud_patterns(self, routes: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Analyze routes to determine if this looks like a CRUD API.

        Returns:
            Tuple of (use_crud_base, resource_name)
        """
        # Look for common CRUD patterns
        paths = [route["path"] for route in routes]
        operation_ids = [route["operation_id"] for route in routes]

        # Check if we have typical CRUD operations by examining method-path combinations
        route_combinations = [(route["method"], route["path"]) for route in routes]

        has_get_list = any(
            method == "GET" and "{" not in path for method, path in route_combinations
        )
        has_get_single = any(
            method == "GET" and "{" in path for method, path in route_combinations
        )
        has_post = any(
            method == "POST" and "{" not in path for method, path in route_combinations
        )  # POST to collection
        has_put_patch = any(
            method in ["PUT", "PATCH"] for method, path in route_combinations
        )
        has_delete = any(method == "DELETE" for method, path in route_combinations)

        crud_score = sum(
            [has_get_list, has_get_single, has_post, has_put_patch, has_delete]
        )

        # Look for typical CRUD operation patterns in operation IDs
        crud_verbs = {"get_", "list_", "create_", "update_", "delete_", "destroy_"}
        crud_operation_patterns = sum(
            [
                any(op_id.lower().startswith(verb) for verb in crud_verbs)
                for op_id in operation_ids
            ]
        )

        # Check for common CRUD operation IDs directly
        common_crud_ids = {"index", "create", "show", "update", "destroy"}
        has_common_crud_ids = any(op_id in common_crud_ids for op_id in operation_ids)

        # Count how many common CRUD operation IDs we have
        common_crud_count = sum(
            1 for op_id in operation_ids if op_id in common_crud_ids
        )

        # Must have both collection-style paths AND CRUD operation names to be considered CRUD
        # Also need at least one basic collection endpoint (list or create on base path)
        base_collection_operations = any(
            (method == "GET" and path.count("/") <= 2 and "{" not in path)  # GET /users
            or (
                method == "POST" and path.count("/") <= 2 and "{" not in path
            )  # POST /users
            for method, path in route_combinations
        )

        # If we have 3+ CRUD operations AND (CRUD operation names OR common CRUD IDs) AND collection-style endpoints
        # OR if we have 3+ common CRUD IDs directly
        use_crud_base = (
            crud_score >= 3
            and (crud_operation_patterns >= 2 or has_common_crud_ids)
            and base_collection_operations
        ) or common_crud_count >= 3

        # Extract resource name from paths or operation IDs
        resource_name = self._extract_resource_name(paths, operation_ids)

        return use_crud_base, resource_name

    def _extract_resource_name(self, paths: List[str], operation_ids: List[str]) -> str:
        """Extract the resource name from paths or operation IDs."""
        # Try to extract from operation IDs first (more reliable)
        for op_id in operation_ids:
            # Look for patterns like 'get_user', 'create_user', etc.
            parts = op_id.split("_")
            if len(parts) >= 2:
                # Skip verbs like 'get', 'create', 'update', 'delete'
                verbs = {"get", "create", "update", "delete", "list", "show", "destroy"}
                for part in parts:
                    if part not in verbs:
                        # Remove plural 's' if present
                        if part.endswith("s") and len(part) > 1:
                            return part[:-1]
                        return part

        # Try to extract from paths as fallback
        for path in paths:
            # Remove leading slash and parameters
            parts = path.strip("/").split("/")
            if parts and parts[0] and not parts[0].startswith("{"):
                # Remove version prefixes like 'v1', 'api'
                resource = parts[0]
                if resource.lower() not in ["api", "v1", "v2", "v3"]:
                    return resource.rstrip(
                        "s"
                    ).lower()  # Remove plural 's' and normalize

        # Final fallback
        return "resource"

    def _map_to_crud_operation(
        self, operation_id: str, method: str, path: str
    ) -> Optional[Dict[str, str]]:
        """
        Map an operation to a CRUD method and parameter extraction.

        Returns:
            Dict with 'crud_method' and 'param_extraction' keys, or None if no mapping
        """

        # Detect if this is a list operation (GET without ID parameter)
        if method == "GET" and "{" not in path:
            return {
                "crud_method": "index(filters=filters)",
                "param_extraction": "# List operation - pass query parameters as filters\n            filters = {k: v for k, v in data.items() if k not in ['auth', 'body']}",
                "operation_name": "list",
            }

        # Detect if this is a show operation (GET with ID parameter)
        elif method == "GET" and "{" in path:
            param_name = self._extract_id_param_name(path)
            return {
                "crud_method": "show(resource_id)",
                "param_extraction": f"# Show operation - extract resource ID\n            resource_id = data.get('{param_name}')\n            if not resource_id:\n                raise ValidationError('Resource ID is required')",
                "operation_name": "read",
            }

        # Create operation (POST)
        elif method == "POST":
            return {
                "crud_method": "create(data=body)",
                "param_extraction": "# Create operation - extract request body\n            body = data.get('body', {})\n            if not body:\n                raise ValidationError('Request body is required')",
                "operation_name": "create",
            }

        # Update operation (PUT/PATCH)
        elif method in ["PUT", "PATCH"]:
            param_name = self._extract_id_param_name(path)
            return {
                "crud_method": "update(resource_id, data=body)",
                "param_extraction": f"# Update operation - extract resource ID and body\n            resource_id = data.get('{param_name}')\n            if not resource_id:\n                raise ValidationError('Resource ID is required')\n            body = data.get('body', {{}})\n            if not body:\n                raise ValidationError('Request body is required')",
                "operation_name": "update",
            }

        # Delete operation (DELETE)
        elif method == "DELETE":
            param_name = self._extract_id_param_name(path)
            return {
                "crud_method": "destroy(resource_id)",
                "param_extraction": f"# Delete operation - extract resource ID\n            resource_id = data.get('{param_name}')\n            if not resource_id:\n                raise ValidationError('Resource ID is required')",
                "operation_name": "delete",
            }

        return None

    def _extract_id_param_name(self, path: str) -> str:
        """Extract the ID parameter name from a path like /users/{user_id}."""
        match = re.search(r"\{([^}]+)\}", path)
        if match:
            return match.group(1)
        return "id"  # fallback

    def _get_class_name(self, resource_name: str = None) -> str:
        """Generate class name from resource name or spec file name."""
        if resource_name and resource_name != "resource":
            # Use resource-based naming: user -> UserService, locations -> LocationService
            singular_name = (
                resource_name.rstrip("s")
                if resource_name.endswith("s")
                else resource_name
            )
            return f"{singular_name.capitalize()}Service"

        # Fallback to file-based naming for non-CRUD APIs
        stem = self.spec_path.stem

        # Convert to PascalCase without removing version info
        # example.yaml -> ExampleService
        # users_v2.yaml -> UsersV2Service
        words = stem.replace("-", "_").split("_")
        class_name = "".join(word.capitalize() for word in words if word)

        return f"{class_name}Service"

    def _should_init_project(self) -> bool:
        """Determine if this should initialize a new project structure."""
        current_dir = Path(".")

        # Check if we're in an empty or minimal directory
        has_main = (current_dir / "main.py").exists()
        has_implementations = (current_dir / "implementations").exists() and any(
            (current_dir / "implementations").iterdir()
        )
        has_specifications_dir = (current_dir / "specifications").exists() and any(
            (current_dir / "specifications").iterdir()
        )

        # Initialize if we don't have main.py AND don't have existing implementations or specifications structure
        return not has_main and not has_implementations and not has_specifications_dir

    def _init_project_structure(
        self, implementation_file: Path, template_data: Dict[str, Any]
    ):
        """Initialize complete project structure."""
        print("🚀 Initializing project structure...")

        # Create main.py
        self._create_main_py(implementation_file, template_data)

        # Move API spec to specifications/ directory if needed
        spec_moved = self._organize_api_spec()

        # Create .gitignore if it doesn't exist
        self._create_gitignore()

        print("✨ Project structure initialized!")
        print("📁 Created:")
        print("   - main.py (FastAPI app entry point)")
        print(f"   - {implementation_file} (implementation)")
        if spec_moved:
            print(f"   - specifications/{self.spec_path.name} (organized API spec)")
        print("🚀 Run with: python main.py")

    def _create_main_py(self, implementation_file: Path, template_data: Dict[str, Any]):
        """Create main.py that sets up and runs the automatic app."""
        class_name = template_data["class_name"]

        # Determine import path for the implementation
        # implementations/user_service.py -> implementations.user_service.UserService
        try:
            # Try to get relative path from current working directory
            rel_path = implementation_file.relative_to(Path.cwd())
            impl_module = str(rel_path.with_suffix("")).replace("/", ".")
        except ValueError:
            # If file is not relative to cwd, use just the filename parts we need
            # Extract the last two parts: implementations/service_name
            parts = implementation_file.parts
            if len(parts) >= 2 and parts[-2] == "implementations":
                impl_module = f"implementations.{implementation_file.stem}"
            else:
                # Fallback: just use the stem
                impl_module = implementation_file.stem

        # Determine API spec path (use organized path if we moved it)
        api_spec_path = (
            f"specifications/{self.spec_path.name}"
            if self._should_organize_spec()
            else str(self.spec_path)
        )

        # Render template
        template = self.jinja_env.get_template("single_spec_main.py.j2")
        main_content = template.render(
            class_name=class_name, impl_module=impl_module, api_spec_path=api_spec_path
        )

        main_file = Path("main.py")
        main_file.write_text(main_content)

    def _should_organize_spec(self) -> bool:
        """Check if the spec should be moved to specifications/ directory."""
        # Only organize if the spec is in the current directory and not already in specifications/
        return self.spec_path.parent == Path(".") and not str(
            self.spec_path
        ).startswith("specifications/")

    def _organize_api_spec(self) -> bool:
        """Move API spec to specifications/ directory if appropriate."""
        if not self._should_organize_spec():
            return False

        # Create specifications directory
        specs_dir = Path("specifications")
        specs_dir.mkdir(exist_ok=True)

        # Move the spec file
        new_spec_path = specs_dir / self.spec_path.name
        if not new_spec_path.exists():
            import shutil

            shutil.move(str(self.spec_path), str(new_spec_path))
            # Update our internal path reference
            self.spec_path = new_spec_path
            return True

        return False

    def _create_gitignore(self):
        """Create a basic .gitignore if it doesn't exist."""
        gitignore_path = Path(".gitignore")
        if gitignore_path.exists():
            return

        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
"""

        gitignore_path.write_text(gitignore_content)

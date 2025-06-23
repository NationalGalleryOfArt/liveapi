"""Prompt building and template handling for OpenAPI spec generation."""

from typing import Dict, Any
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class PromptBuilder:
    """Builds prompts for LLM-based OpenAPI spec generation."""

    def __init__(self):
        """Initialize the prompt builder with templates."""
        # Setup Jinja2 environment for templates
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def build_prompt(self, api_info: Dict[str, Any]) -> str:
        """Build prompt for LLM based on API information.

        Args:
            api_info: Dictionary containing API details

        Returns:
            Formatted prompt string
        """
        template = self.jinja_env.get_template("api_spec_prompt.j2")

        return template.render(
            name=api_info.get("name", "My API"),
            description=api_info.get("description", "API description"),
            endpoint_descriptions=api_info.get("endpoint_descriptions", ""),
        )

    def build_spec_from_template(
        self, llm_response: Dict[str, Any], name: str = None, description: str = None
    ) -> Dict[str, Any]:
        """Build complete OpenAPI spec from LLM response using our template.

        Args:
            llm_response: Dictionary containing paths and schemas
            name: API name
            description: API description

        Returns:
            Complete OpenAPI specification as dict
        """
        import json

        # Load the base template
        template = self.jinja_env.get_template("openapi_base_template.j2")

        # Get project config for API base URL if available
        try:
            from pathlib import Path

            config_path = Path(".liveapi/config.json")
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                    api_base_url = config.get("api_base_url", "api.example.com")
            else:
                api_base_url = "api.example.com"
        except:
            api_base_url = "api.example.com"

        # Use provided name/description or defaults
        title = name or "API Service"
        desc = description or "API Service"

        # Render the template
        spec_content = template.render(
            title=title,
            description=desc,
            api_base_url=api_base_url,
            paths=llm_response["paths"],
            schemas=llm_response["schemas"],
        )

        return json.loads(spec_content)

    def add_server_environments(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Add multiple server environments to the OpenAPI spec.

        Args:
            spec: OpenAPI specification dict

        Returns:
            Updated OpenAPI specification with servers
        """
        # Get base URL from project config if available
        from ..metadata_manager import MetadataManager

        try:
            metadata_manager = MetadataManager()
            config = metadata_manager.load_config()
            api_base_url = config.api_base_url if config else None
        except:
            api_base_url = None

        # Build server list
        servers = [
            {"url": "http://localhost:8000", "description": "Development server"}
        ]

        if api_base_url:
            # Add environment-specific servers
            servers.extend(
                [
                    {
                        "url": f"https://test-{api_base_url}",
                        "description": "Test server",
                    },
                    {
                        "url": f"https://staging-{api_base_url}",
                        "description": "Staging server",
                    },
                    {
                        "url": f"https://{api_base_url}",
                        "description": "Production server",
                    },
                ]
            )

        # Add servers to spec
        spec["servers"] = servers
        return spec

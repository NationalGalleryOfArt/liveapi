"""Test that template files can be loaded correctly."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader


class TestTemplateLoading:
    """Test that Jinja2 templates can be loaded with correct names."""

    def test_template_files_exist(self):
        """Test that all expected template files exist."""
        template_dir = (
            Path(__file__).parent.parent / "src" / "liveapi" / "sync" / "templates"
        )

        expected_templates = [
            "database.py.j2",
            "default_resource_subclass.py.j2",
            "main.py.j2",
            "requirements_sql.txt.j2",
            "sql_model_resource_subclass.py.j2",
        ]

        for template_name in expected_templates:
            template_file = template_dir / template_name
            assert template_file.exists(), f"Template {template_name} does not exist"
            assert template_file.is_file(), f"Template {template_name} is not a file"

    def test_templates_can_be_loaded(self):
        """Test that templates can be loaded by Jinja2."""
        template_dir = (
            Path(__file__).parent.parent / "src" / "liveapi" / "sync" / "templates"
        )
        env = Environment(loader=FileSystemLoader(template_dir))

        # Test loading the renamed templates
        sql_template = env.get_template("sql_model_resource_subclass.py.j2")
        default_template = env.get_template("default_resource_subclass.py.j2")

        assert sql_template is not None
        assert default_template is not None

    def test_old_template_names_dont_exist(self):
        """Test that old template names no longer exist."""
        template_dir = (
            Path(__file__).parent.parent / "src" / "liveapi" / "sync" / "templates"
        )

        old_names = ["sql_model_service.py.j2", "implementation.py.j2"]

        for old_name in old_names:
            old_file = template_dir / old_name
            assert not old_file.exists(), f"Old template {old_name} still exists"

    def test_templates_can_render_with_basic_context(self):
        """Test that templates can render with basic context."""
        template_dir = (
            Path(__file__).parent.parent / "src" / "liveapi" / "sync" / "templates"
        )
        env = Environment(loader=FileSystemLoader(template_dir))

        # Test basic rendering with minimal context
        sql_template = env.get_template("sql_model_resource_subclass.py.j2")
        default_template = env.get_template("default_resource_subclass.py.j2")

        test_context = {
            "resource_name": "test",
            "class_name": "TestService",
            "model_name": "Test",
        }

        # Should not raise exceptions
        sql_content = sql_template.render(**test_context)
        default_content = default_template.render(**test_context)

        assert len(sql_content) > 0
        assert len(default_content) > 0
        assert "TestService" in sql_content
        assert "TestService" in default_content

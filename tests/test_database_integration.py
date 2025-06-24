"""Tests for database integration features."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.liveapi.implementation.database import DatabaseManager, get_database_manager
from src.liveapi.implementation.pydantic_generator import PydanticGenerator
from src.liveapi.implementation.liveapi_router import LiveAPIRouter
from src.liveapi.generator.interactive import InteractiveGenerator
from src.liveapi.metadata.models import ProjectConfig

# Check if SQLModel is available
try:
    from sqlmodel import Session
    HAS_SQLMODEL = True
except ImportError:
    HAS_SQLMODEL = False


class TestDatabaseManager:
    """Test the DatabaseManager class."""

    def test_default_database_url(self):
        """Test default database URL configuration."""
        db_manager = DatabaseManager()
        assert db_manager.database_url.startswith("sqlite:")

    def test_custom_database_url(self):
        """Test custom database URL configuration."""
        custom_url = "postgresql://user:pass@localhost/test"
        db_manager = DatabaseManager(custom_url)
        assert db_manager.database_url == custom_url

    def test_engine_creation(self):
        """Test database engine creation."""
        db_manager = DatabaseManager()
        engine = db_manager.get_engine()
        assert engine is not None
        # Second call should return same engine
        assert db_manager.get_engine() is engine

    def test_session_generator(self):
        """Test database session generator."""
        db_manager = DatabaseManager()
        sessions = list(db_manager.get_session())
        assert len(sessions) == 1

    def test_close(self):
        """Test database cleanup."""
        db_manager = DatabaseManager()
        db_manager.get_engine()
        db_manager.close()
        assert db_manager.engine is None
        assert db_manager._initialized is False


class TestPydanticGeneratorWithBackends:
    """Test PydanticGenerator with different backends."""

    def test_default_backend_initialization(self):
        """Test PydanticGenerator with default backend."""
        generator = PydanticGenerator("default")
        assert generator.backend_type == "default"
        assert generator._sqlmodel_base is None

    @pytest.mark.skipif(not HAS_SQLMODEL, reason="SQLModel not available in test environment")
    def test_sqlmodel_backend_initialization(self):
        """Test PydanticGenerator with SQLModel backend."""
        generator = PydanticGenerator("sqlmodel")
        assert generator.backend_type == "sqlmodel"
        assert generator._sqlmodel_base is not None

    def test_sqlmodel_without_dependency(self):
        """Test SQLModel backend without sqlmodel installed."""
        with patch("builtins.__import__", side_effect=ImportError("No module named 'sqlmodel'")):
            with pytest.raises(ImportError, match="SQLModel is required"):
                PydanticGenerator("sqlmodel")

    def test_model_generation_default_backend(self):
        """Test model generation with default backend."""
        generator = PydanticGenerator("default")
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        model = generator.generate_model_from_schema(schema, "TestModel")
        assert model is not None
        assert hasattr(model, "model_fields") or hasattr(model, "__fields__")


class TestLiveAPIRouterBackendSelection:
    """Test LiveAPIRouter backend configuration."""

    def test_default_backend_config(self):
        """Test router with default backend configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.cwd", return_value=Path(temp_dir)):
                router = LiveAPIRouter()
                assert router.backend_type == "default"

    def test_sqlmodel_backend_config(self):
        """Test router with SQLModel backend configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_dir = temp_path / ".liveapi"
            metadata_dir.mkdir()
            
            config_file = metadata_dir / "config.json"
            config_data = {"backend_type": "sqlmodel"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)
            
            with patch("pathlib.Path.cwd", return_value=temp_path):
                router = LiveAPIRouter()
                assert router.backend_type == "sqlmodel"

    def test_service_dependency_creation_default(self):
        """Test service dependency creation with default backend."""
        from pydantic import BaseModel

        class PydanticTestModel(BaseModel):
            name: str

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pathlib.Path.cwd", return_value=Path(temp_dir)):
                router = LiveAPIRouter()
                service_dependency = router._create_service_dependency(PydanticTestModel, "test")
                service = service_dependency()
                
                from src.liveapi.implementation.default_resource_service import DefaultResourceService
                assert isinstance(service, DefaultResourceService)

    @pytest.mark.skipif(not HAS_SQLMODEL, reason="SQLModel not available in test environment")
    def test_service_dependency_creation_sqlmodel(self):
        """Test service dependency creation with SQLModel backend."""
        from sqlmodel import SQLModel, Field

        class SQLModelForDependencyTest(SQLModel, table=True):
            __tablename__ = "sql_model_for_dependency_test"
            id: str = Field(primary_key=True)
            name: str

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            metadata_dir = temp_path / ".liveapi"
            metadata_dir.mkdir()
            
            config_file = metadata_dir / "config.json"
            config_data = {"backend_type": "sqlmodel"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            with patch("pathlib.Path.cwd", return_value=temp_path):
                router = LiveAPIRouter()
                service_dependency = router._create_service_dependency(SQLModelForDependencyTest, "test")

                # Mock the session dependency
                mock_session = MagicMock(spec=Session)
                
                # We need to inject the dependency manually for testing
                service = service_dependency(session=mock_session)
                
                from src.liveapi.implementation.sql_model_resource_service import SQLModelResourceService
                assert isinstance(service, SQLModelResourceService)


class TestInteractiveGeneratorWithBackends:
    """Test InteractiveGenerator with backend selection."""

    def test_backend_selection_in_api_info(self):
        """Test that backend selection is included in API info."""
        generator = InteractiveGenerator(None)
        
        inputs = iter([
            "users",
            "User management",
            "Users API",
            "User management API",
            "2",
            '{"name": "string", "email": "string"}',
            "",
            "",
            '[{"name": "John", "email": "john@example.com"}]',
            "",
            "",
        ])
        
        with patch("builtins.input", side_effect=inputs):
            with patch("src.liveapi.metadata_manager.MetadataManager") as mock_manager:
                mock_config = MagicMock()
                mock_config.api_base_url = None
                mock_config.backend_type = "default"
                mock_manager.return_value.load_config.return_value = mock_config
                mock_manager.return_value.save_config.return_value = None
                
                api_info = generator.collect_api_info()
                
        assert "backend_type" in api_info
        assert api_info["backend_type"] == "sqlmodel"


class TestDatabaseIntegrationEndToEnd:
    """End-to-end integration tests."""

    def test_global_database_manager(self):
        """Test global database manager functionality."""
        import src.liveapi.implementation.database as db_module
        db_module._db_manager = None
        
        manager1 = get_database_manager()
        manager2 = get_database_manager()
        
        assert manager1 is manager2

    def test_database_initialization(self):
        """Test database table initialization."""
        from src.liveapi.implementation.database import init_database, close_database
        
        init_database()
        close_database()

    def test_project_config_with_backend_type(self):
        """Test ProjectConfig includes backend_type field."""
        config = ProjectConfig(
            project_name="test",
            created_at="2023-01-01T00:00:00Z",
            backend_type="sqlmodel"
        )
        
        assert config.backend_type == "sqlmodel"
        
        config_default = ProjectConfig(
            project_name="test",
            created_at="2023-01-01T00:00:00Z"
        )
        
        assert config_default.backend_type == "default"


@pytest.mark.skipif(not HAS_SQLMODEL, reason="SQLModel integration tests require SQLModel dependency")
class TestSQLModelIntegration:
    """Integration tests for SQLModel backend (requires sqlmodel package)."""

    def test_sqlmodel_resource_service_creation(self):
        """Test SQLModelResourceService instantiation."""
        from src.liveapi.implementation.sql_model_resource_service import SQLModelResourceService
        from sqlmodel import SQLModel, Field

        class SQLModelForServiceTest(SQLModel, table=True):
            __tablename__ = "test_model_creation"
            id: str = Field(primary_key=True)
            name: str

        mock_session = MagicMock(spec=Session)
        service = SQLModelResourceService(SQLModelForServiceTest, "test", session=mock_session)
        assert service.resource_name == "test"
        assert service.model == SQLModelForServiceTest
        assert service.session == mock_session

    @pytest.mark.asyncio
    async def test_sqlmodel_crud_operations(self):
        """Test basic CRUD operations with SQLModel service."""
        # This would require actual SQLModel setup and would be more complex
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

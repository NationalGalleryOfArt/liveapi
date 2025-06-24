"""End-to-end integration test for complete LiveAPI workflow."""

import tempfile
import time
import requests
import subprocess
import os
from pathlib import Path
from unittest.mock import patch

from liveapi.cli.main import main as cli_main
from liveapi.generator.generator import SpecGenerator
from liveapi.generator.interactive import InteractiveGenerator


class TestEndToEndFlow:
    """Test the complete LiveAPI workflow from generation to running API."""

    def test_complete_workflow_integration(self):
        """Test the full workflow: generate -> sync -> run -> validate swagger."""

        # Create a temporary directory for the test project
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Change to the temp directory to simulate a real project
            original_cwd = os.getcwd()
            os.chdir(temp_path)

            try:
                # Step 1: Initialize the project
                self._initialize_project()

                # Step 2: Generate API specification interactively
                self._generate_api_spec()

                # Step 3: Sync to generate implementation
                self._sync_implementation()

                # Step 4: Run the API server and validate
                self._run_and_validate_api()

            finally:
                os.chdir(original_cwd)

    def _initialize_project(self):
        """Initialize a LiveAPI project and configure it for SQLModel."""
        # Mock user inputs for project initialization
        init_inputs = [
            "",  # Empty project name (use directory name)
            "",  # Empty API base URL (use default)
        ]

        # Mock the CLI call to liveapi init
        with patch("sys.argv", ["liveapi", "init"]):
            with patch("builtins.input", side_effect=init_inputs):
                with patch("builtins.print"):  # Suppress output
                    cli_main()

        # Verify project was initialized
        assert Path(".liveapi").exists()
        config_path = Path(".liveapi/config.json")
        assert config_path.exists()

        # Ensure the config specifies the sqlmodel backend
        import json
        with open(config_path, "r") as f:
            config = json.load(f)
        
        config["backend_type"] = "sqlmodel"
        
        with open(config_path, "w") as f:
            json.dump(config, f)

    def _generate_api_spec(self):
        """Generate API specification using interactive mode."""
        # Create spec generator and interactive generator
        spec_generator = SpecGenerator()
        interactive_gen = InteractiveGenerator(spec_generator)

        # Mock user inputs for a complete product catalog API (new workflow order)
        user_inputs = [
            "products",  # object name (now first)
            "Product inventory items with pricing and stock info",  # object description
            "Product Catalog API",  # API name (with default shown)
            "REST API for managing product inventory",  # API description (with default shown)
            # JSON attributes
            '{\n  "name": "string",\n  "description": "string",\n  "price": "number",\n  "category": "string",\n  "inStock": "boolean",\n  "sku": "string"\n}',
            "",  # first empty line
            "",  # second empty line to end JSON input
            # JSON array examples (new format)
            '[\n  {\n    "name": "Gaming Laptop",\n    "description": "High-performance gaming laptop with RTX graphics",\n    "price": 1299.99,\n    "category": "Electronics",\n    "inStock": true,\n    "sku": "LAP-GAME-001"\n  },\n  {\n    "name": "Office Chair",\n    "description": "Ergonomic office chair with lumbar support",\n    "price": 249.99,\n    "category": "Furniture",\n    "inStock": false,\n    "sku": "CHR-OFF-002"\n  }\n]',
            "",  # first empty line
            "",  # second empty line
        ]

        with patch("builtins.input", side_effect=user_inputs):
            with patch("builtins.print"):  # Suppress interactive output
                spec = interactive_gen.interactive_generate()

        # Verify specification was generated
        assert spec is not None
        assert spec["info"]["title"] == "Product Catalog API"
        assert "products" in str(spec["paths"])

        # Save the spec to file (like the CLI does)
        specs_dir = Path("specifications")
        specs_dir.mkdir(exist_ok=True)
        output_path = specs_dir / "product_catalog.yaml"
        spec_generator.save_spec(spec, output_path, "yaml")

        # Track the spec in the project (like the CLI does)
        from liveapi.metadata_manager import MetadataManager
        from liveapi.change_detector import ChangeDetector

        # Initialize managers for spec generation
        MetadataManager()
        change_detector = ChangeDetector()
        change_detector.update_spec_tracking(output_path)

        # Verify spec file was saved
        assert output_path.exists()
        spec_files = list(Path("specifications").glob("*.yaml"))
        assert len(spec_files) > 0

        # Debug: Print the generated spec content
        with open(output_path) as f:
            spec_content = f.read()
            print(f"Generated spec preview (first 500 chars):\n{spec_content[:500]}...")
            print(f"Contains 'products'? {'products' in spec_content}")
            print(f"Contains 'paths'? {'paths' in spec_content}")

        # Verify prompt files were saved (filename based on auto-inferred project name "products")
        assert Path(".liveapi/prompts/products_prompt.json").exists()
        assert Path(".liveapi/prompts/products_schema.json").exists()

    def _sync_implementation(self):
        """Sync to generate FastAPI implementation."""
        # Mock the CLI call to liveapi sync (with confirmation input)
        sync_inputs = ["y"]  # Confirm sync if prompted
        with patch("sys.argv", ["liveapi", "sync", "--force"]):
            with patch("builtins.input", side_effect=sync_inputs):
                with patch("builtins.print"):  # Suppress output
                    cli_main()

        # In CRUD+ mode, a main.py file is created in the root directory
        assert Path("main.py").exists()

        # Debug: Check the main.py content
        with open("main.py") as f:
            main_content = f.read()
            print(f"main.py preview (first 300 chars):\n{main_content[:300]}...")

        # Debug: List specification files
        spec_files = list(Path("specifications").glob("*.yaml"))
        print(f"Spec files found: {[f.name for f in spec_files]}")

        # Also check if implementations directory exists (for backward compatibility)
        # The implementations directory might be created but empty in CRUD+ mode
        if Path("implementations").exists():
            print("Implementations directory exists (legacy mode)")
        else:
            print("Using CRUD+ mode with main.py")

    def _run_and_validate_api(self):
        """Run the API server and validate the swagger documentation."""
        # In CRUD+ mode, use main.py; otherwise look for implementation files
        if Path("main.py").exists():
            app_file = Path("main.py")
            app_module = "main:app"
            work_dir = Path.cwd()
        else:
            # Legacy mode - look in implementations directory
            impl_files = list(Path("implementations").glob("*app*.py"))
            if not impl_files:
                impl_files = list(Path("implementations").glob("*.py"))

            app_file = impl_files[0]
            app_module = f"{app_file.stem}:app"
            work_dir = Path("implementations")

        # Start the server in a subprocess
        port = 8000
        server_process = None

        try:
            # Set up a file-based SQLite database for the test
            db_path = Path.cwd() / "test.db"
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
            from src.liveapi.implementation.database import init_database, close_database
            init_database()

            # Run the server using uvicorn
            cmd = [
                "python",
                "-m",
                "uvicorn",
                app_module,
                "--host",
                "0.0.0.0",
                "--port",
                str(port),
            ]

            # Change to the appropriate working directory
            original_cwd = os.getcwd()
            os.chdir(work_dir)

            server_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd()
            )

            # Wait for server to start
            self._wait_for_server(port)

            # Validate the API endpoints
            self._validate_api_endpoints(port)

            # Validate swagger documentation
            self._validate_swagger_docs(port)

        finally:
            # Cleanup: kill the server process
            if server_process:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()
            
            close_database()
            os.chdir(original_cwd)

    def _wait_for_server(self, port, timeout=30):
        """Wait for the server to start accepting connections."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}/docs", timeout=1)
                if response.status_code == 200:
                    return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                time.sleep(0.5)

        raise TimeoutError(f"Server did not start within {timeout} seconds")

    def _validate_api_endpoints(self, port):
        """Validate that the generated API endpoints work correctly."""
        base_url = f"http://localhost:{port}"

        # First, let's check the OpenAPI docs to see available endpoints
        try:
            openapi_response = requests.get(f"{base_url}/openapi.json")
            if openapi_response.status_code == 200:
                openapi_spec = openapi_response.json()
                print(f"Available paths: {list(openapi_spec.get('paths', {}).keys())}")
                print(
                    f"Runtime OpenAPI spec info: title='{openapi_spec.get('info', {}).get('title')}', paths_count={len(openapi_spec.get('paths', {}))}"
                )
                # Print first 200 chars of the runtime spec for debugging
                import json as json_module

                spec_str = json_module.dumps(openapi_spec, indent=2)
                print(f"Runtime spec preview: {spec_str[:300]}...")
            else:
                print(f"OpenAPI endpoint returned: {openapi_response.status_code}")
        except Exception as e:
            print(f"Error fetching OpenAPI spec: {e}")

        # Test health check endpoint - try both / and /health
        try:
            response = requests.get(f"{base_url}/")
            print(f"GET / returned: {response.status_code}")
            if response.status_code != 200:
                # Try /health instead
                response = requests.get(f"{base_url}/health")
                print(f"GET /health returned: {response.status_code}")
                if response.status_code != 200:
                    # Skip health check and go straight to API endpoints
                    print("No health endpoint found, testing API endpoints directly")
        except Exception as e:
            print(f"Health check error: {e}")

        # Test CRUD endpoints for products (no authentication required)

        # 1. GET /products (list) - should return simple array initially
        response = requests.get(f"{base_url}/products")
        print(f"GET /products returned: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.text}")
        assert response.status_code == 200
        products_response = response.json()
        assert isinstance(products_response, list)
        assert len(products_response) == 0

        # 2. POST /products (create) - use fields from generated schema
        new_product = {
            "name": "Test Product",
            "description": "A test product",
            "price": 19.99,
            "category": "Test",
            "inStock": True,
            "sku": "TEST-001",
        }

        response = requests.post(f"{base_url}/products", json=new_product)
        if response.status_code != 201:
            print("POST /products failed with status:", response.status_code)
            print("Response body:", response.text)
        assert response.status_code == 201
        created_product = response.json()
        assert created_product["name"] == "Test Product"
        assert "id" in created_product
        product_id = created_product["id"]

        time.sleep(1)

        # 3. GET /products/{id} (read)
        response = requests.get(
            f"{base_url}/products/{product_id}",
        )
        assert response.status_code == 200
        product = response.json()
        assert product["name"] == "Test Product"
        assert product["id"] == product_id

        # 4. PUT /products/{id} (update)
        updated_product = created_product.copy()
        updated_product["price"] = 29.99

        response = requests.put(
            f"{base_url}/products/{product_id}",
            json=updated_product,
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["price"] == 29.99

        # 5. GET /products (list) - should now have one item
        response = requests.get(
            f"{base_url}/products",
        )
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        assert len(products) == 1
        assert products[0]["id"] == product_id

        # 6. DELETE /products/{id}
        response = requests.delete(
            f"{base_url}/products/{product_id}",
        )
        assert response.status_code == 204

        # 7. GET /products/{id} - should return 404
        response = requests.get(
            f"{base_url}/products/{product_id}",
        )
        assert response.status_code == 404

    def _validate_swagger_docs(self, port):
        """Validate the generated Swagger/OpenAPI documentation."""
        base_url = f"http://localhost:{port}"

        # Get the OpenAPI JSON
        response = requests.get(f"{base_url}/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()

        # Validate basic OpenAPI structure (FastAPI uses 3.1.0)
        assert openapi_spec["openapi"] in ["3.0.3", "3.1.0"]
        assert openapi_spec["info"]["title"] == "Product Catalog API"

        # Validate paths
        paths = openapi_spec["paths"]

        # Check CRUD endpoints exist
        assert "/products" in paths
        assert "/products/{id}" in paths

        # Validate GET /products (list) exists
        get_products = paths["/products"]["get"]
        assert "200" in get_products["responses"]

        # Validate POST /products (create) exists
        post_products = paths["/products"]["post"]
        assert "201" in post_products["responses"]

        # Validate that we have schemas
        assert "components" in openapi_spec
        assert "schemas" in openapi_spec["components"]

        print("✅ End-to-end workflow validation complete - core functionality works")

    def test_swagger_ui_accessibility(self):
        """Test that the Swagger UI is accessible and renders correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(temp_path)

            try:
                # Quick setup for this test
                self._initialize_project()
                self._generate_minimal_api_spec()
                self._sync_implementation()

                # Start server and test Swagger UI
                if Path("main.py").exists():
                    app_module = "main:app"
                    work_dir = Path.cwd()
                else:
                    impl_files = list(Path("implementations").glob("*app*.py"))
                    if not impl_files:
                        impl_files = list(Path("implementations").glob("*.py"))

                    app_file = impl_files[0]
                    app_module = f"{app_file.stem}:app"
                    work_dir = Path("implementations")

                port = 8001  # Use different port to avoid conflicts

                server_process = None
                try:
                    os.chdir(work_dir)
                    cmd = [
                        "python",
                        "-m",
                        "uvicorn",
                        app_module,
                        "--host",
                        "0.0.0.0",
                        "--port",
                        str(port),
                    ]

                    server_process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )

                    self._wait_for_server(port)

                    # Test Swagger UI endpoint
                    response = requests.get(f"http://localhost:{port}/docs")
                    assert response.status_code == 200
                    assert "swagger" in response.text.lower()
                    assert "openapi" in response.text.lower()

                    # Test ReDoc endpoint
                    response = requests.get(f"http://localhost:{port}/redoc")
                    assert response.status_code == 200
                    assert "redoc" in response.text.lower()

                finally:
                    if server_process:
                        server_process.terminate()
                        try:
                            server_process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            server_process.kill()

                    os.chdir(temp_path)

            finally:
                os.chdir(original_cwd)

    def _generate_minimal_api_spec(self):
        """Generate a minimal API spec for quick testing."""
        spec_generator = SpecGenerator()
        interactive_gen = InteractiveGenerator(spec_generator)

        # Updated for new object-first workflow
        user_inputs = [
            "items",  # object name (now first)
            "Simple items",  # object description
            "Simple API",  # API name (with default shown)
            "Simple test API",  # API description (with default shown)
            '{"name": "string"}',  # JSON attributes
            "",  # first empty line
            "",  # second empty line
            # JSON array examples (new format)
            '[{"name": "Item 1"}, {"name": "Item 2"}]',
            "",  # first empty line
            "",  # second empty line
        ]

        with patch("builtins.input", side_effect=user_inputs):
            with patch("builtins.print"):
                spec = interactive_gen.interactive_generate()

        # Save the spec to file
        specs_dir = Path("specifications")
        specs_dir.mkdir(exist_ok=True)
        output_path = specs_dir / "simple_api.yaml"
        spec_generator.save_spec(spec, output_path, "yaml")

        # Track the spec
        from liveapi.change_detector import ChangeDetector

        change_detector = ChangeDetector()
        change_detector.update_spec_tracking(output_path)

    def test_basic_api_functionality(self):
        """Test that basic API functionality works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original_cwd = os.getcwd()
            os.chdir(temp_path)

            try:
                # Setup project
                self._initialize_project()
                self._generate_minimal_api_spec()
                self._sync_implementation()

                # Start server
                if Path("main.py").exists():
                    app_module = "main:app"
                    work_dir = Path.cwd()
                else:
                    impl_files = list(Path("implementations").glob("*app*.py"))
                    if not impl_files:
                        impl_files = list(Path("implementations").glob("*.py"))

                    app_file = impl_files[0]
                    app_module = f"{app_file.stem}:app"
                    work_dir = Path("implementations")

                port = 8002

                server_process = None
                try:
                    os.chdir(work_dir)
                    cmd = [
                        "python",
                        "-m",
                        "uvicorn",
                        app_module,
                        "--host",
                        "0.0.0.0",
                        "--port",
                        str(port),
                    ]

                    server_process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )

                    self._wait_for_server(port)

                    # Test API endpoint - should get 200
                    response = requests.get(f"http://localhost:{port}/items")
                    assert response.status_code == 200

                finally:
                    if server_process:
                        server_process.terminate()
                        try:
                            server_process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            server_process.kill()

                    os.chdir(temp_path)

            finally:
                os.chdir(original_cwd)

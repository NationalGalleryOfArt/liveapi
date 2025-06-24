"""UI tests for the LiveAPI Designer using Playwright."""

import json
import time
import subprocess
import pytest
from pathlib import Path


class TestDesignerUI:
    """Test the LiveAPI Designer UI functionality."""

    @pytest.fixture(scope="class")
    def server_process(self):
        """Start the designer server for testing."""
        server_dir = Path(__file__).parent.parent / "designer"
        server_process = subprocess.Popen(
            ["python", "server.py", "8890"],  # Use a different port for testing
            cwd=str(server_dir)
        )
        
        # Wait for server to start
        time.sleep(2)
        
        yield server_process
        
        # Clean up
        server_process.terminate()
        server_process.wait()

    def test_generate_api_button_refreshes_preview(self, page, server_process):
        """Test that clicking the Generate API button refreshes the preview."""
        # Navigate to the designer page
        page.goto("http://localhost:8890/designer.html")
        
        # Wait for page to load
        page.wait_for_selector("#root")
        
        # Modify the JSON in the textarea
        test_api_json = json.dumps({
            "api_name": "Modified Test API",
            "api_description": "Modified API for testing",
            "objects": [
                {
                    "name": "modified_tests",
                    "description": "Modified test objects",
                    "fields": {
                        "name": "string",
                        "value": "number"
                    },
                    "example": {
                        "name": "Modified Test Object",
                        "value": 100
                    }
                }
            ]
        }, indent=2)
        
        # Clear and set the textarea value
        page.fill("textarea", test_api_json)
        
        # Click the Generate API button
        page.click("button:has-text('Generate API')")
        
        # Wait for generation to complete (look for "Generated!" text)
        page.wait_for_selector("button:has-text('Generated!')", state="visible", timeout=5000)
        
        # Wait for the button to return to normal state
        page.wait_for_selector("button:has-text('Generate API')", state="visible", timeout=5000)
        
        # Get the iframe
        iframe = page.frame_locator("iframe")
        
        # Wait for the iframe to load
        time.sleep(2)  # Give the iframe time to refresh
        
        # Verify the preview shows the modified API (check for API title in the iframe)
        iframe.locator("div.information-container span:has-text('Modified Test API')").wait_for(timeout=10000)
        
        # Verify the modified endpoint is shown
        iframe.locator("span.opblock-summary-path:has-text('/modified_tests')").wait_for(timeout=10000)
        
        # Verify POST operation uses 201 Created
        # First expand the POST endpoint
        iframe.locator("div.opblock-summary[data-path='/modified_tests'][data-method='post']").click()
        
        # Check for 201 response code
        iframe.locator("table.responses-table td.response-col_status:has-text('201')").wait_for(timeout=5000)
        
        # Verify DELETE operation uses 204 No Content
        # First collapse the POST endpoint and expand the DELETE endpoint
        iframe.locator("div.opblock-summary[data-path='/modified_tests'][data-method='post']").click()
        iframe.locator("div.opblock-summary[data-path='/modified_tests/{id}'][data-method='delete']").click()
        
        # Check for 204 response code
        iframe.locator("table.responses-table td.response-col_status:has-text('204')").wait_for(timeout=5000)
        
        # Verify error responses have correct examples
        # Check the 400 error response
        iframe.locator("table.responses-table tr[data-code='400'] button.model-box-control").click()
        
        # Verify the example shows "Bad Request" with status 400
        iframe.locator("div.example:has-text('\"title\": \"Bad Request\"')").wait_for(timeout=5000)
        iframe.locator("div.example:has-text('\"status\": 400')").wait_for(timeout=5000)
        
        # Check the 401 error response
        iframe.locator("table.responses-table tr[data-code='401'] button.model-box-control").click()
        
        # Verify the example shows "Unauthorized" with status 401
        iframe.locator("div.example:has-text('\"title\": \"Unauthorized\"')").wait_for(timeout=5000)
        iframe.locator("div.example:has-text('\"status\": 401')").wait_for(timeout=5000)
        
        # Check the 500 error response
        iframe.locator("table.responses-table tr[data-code='500'] button.model-box-control").click()
        
        # Verify the example shows "Internal Server Error" with status 500
        iframe.locator("div.example:has-text('\"title\": \"Internal Server Error\"')").wait_for(timeout=5000)
        iframe.locator("div.example:has-text('\"status\": 500')").wait_for(timeout=5000)
        
        # Check the 503 error response
        iframe.locator("table.responses-table tr[data-code='503'] button.model-box-control").click()
        
        # Verify the example shows "Service Unavailable" with status 503
        iframe.locator("div.example:has-text('\"title\": \"Service Unavailable\"')").wait_for(timeout=5000)
        iframe.locator("div.example:has-text('\"status\": 503')").wait_for(timeout=5000)

# LiveAPI Designer

A browser-based tool for designing APIs with LiveAPI, fully integrated with the project workflow.

## Features

- Design APIs using a simple JSON format
- Generate OpenAPI specifications with a single click
- Preview the generated documentation in real-time
- Automatically save specifications to your project
- Generate implementation files with one click
- No build process or complex setup required

## Getting Started

### Option 1: Using the LiveAPI CLI (Recommended)

1. Run the designer through the LiveAPI CLI:
   ```bash
   liveapi designer
   ```

2. If your project isn't initialized yet, you'll be prompted to set it up:
   ```
   Project name: My API Project
   API base URL: api.example.com
   ```

3. The designer will open in your browser automatically.

4. Edit the JSON in the left panel, click "Preview API Spec", and see the preview update automatically.

5. Click "Scaffold Application" to generate implementation files for your project.

### Option 2: Using the Server Directly

1. Start the server:
   ```bash
   python server.py
   ```

2. Open the designer in your browser:
   ```
   http://localhost:8888/designer.html
   ```

3. Edit the JSON in the left panel, click "Preview API Spec", and see the preview update automatically.

4. Note: When running the server directly, project integration features may not be available.

### Option 3: Command-Line Approach (No Server)

1. Open `designer.html` directly in your browser.

2. Edit the JSON in the left panel and click "Scaffold Application".

3. Save the JSON to a file (e.g., `my_api.json`).

4. Run the generator script:
   ```bash
   python generate_from_json.py my_api.json
   ```

5. Click "Refresh Preview" in the UI to see the updated documentation.

## Project Integration

The Designer now integrates with your LiveAPI project workflow:

1. **Project Initialization**: If your project isn't initialized, the Designer will help you set it up.

2. **Automatic Specification Saving**: Generated OpenAPI specs are automatically saved to your project's `specifications/` directory.

3. **Design JSON Saving**: Your API design JSON is saved to `.liveapi/prompts/` for future reference.

4. **Implementation Generation**: Click "Scaffold Application" to generate implementation files based on your API specification.

## JSON Format

The designer uses a simple JSON format:

```json
{
  "api_name": "My API",
  "api_description": "A simple API for managing resources",
  "objects": [
    {
      "name": "items",
      "description": "Items in the system",
      "fields": {
        "name": "string",
        "description": "string",
        "price": "number",
        "active": "boolean"
      },
      "example": {
        "name": "Widget A",
        "description": "A standard widget",
        "price": 19.99,
        "active": true
      }
    }
  ]
}
```

## Example APIs

The designer includes several example JSON files:

- `demo_api.json` - A library management API
- `books_api.json` - A bookstore API
- `test_api.json` - A simple test API

To use these examples, open the file and copy its contents into the JSON editor in the designer.

## Troubleshooting

- **Preview not updating**: Make sure the server is running and try clicking the "Refresh Preview" button.
- **Server errors**: Check the terminal where you're running the server for error messages.
- **Import errors**: Make sure you're running the scripts from the project root directory.
- **Scaffold Application not working**: Ensure your project is properly initialized with `liveapi init`.

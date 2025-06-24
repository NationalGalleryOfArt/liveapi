# LiveAPI Serverless Designer

A simple, browser-based tool for designing APIs with LiveAPI.

## Features

- Design APIs using a simple JSON format
- Generate OpenAPI specifications with a single click
- Preview the generated documentation in real-time
- No build process or complex setup required

## Getting Started

### Option 1: Using the Server (Recommended)

1. Start the server:
   ```bash
   python server.py
   ```

2. Open the designer in your browser:
   ```
   http://localhost:8888/designer.html
   ```

3. Edit the JSON in the left panel, click "Generate API", and see the preview update automatically. The preview will also automatically refresh when you first load the page.

### Option 2: Command-Line Approach (No Server)

1. Open `designer.html` directly in your browser.

2. Edit the JSON in the left panel and click "Copy JSON".

3. Save the JSON to a file (e.g., `my_api.json`).

4. Run the generator script:
   ```bash
   python generate_from_json.py my_api.json
   ```

5. Click "Refresh Preview" in the UI to see the updated documentation.

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

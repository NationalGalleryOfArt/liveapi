# LiveAPI Designer

A visual designer for creating and managing LiveAPI resources.

## Project Structure

The LiveAPI Designer has been refactored to be more modular while maintaining compatibility with browser environments:

```
designer/
├── index.html           # Main HTML file with all React components
├── styles/
│   └── main.css         # Extracted CSS styles
├── preview.html         # OpenAPI preview page
└── server.py            # Python server for the designer
```

## Component Structure

While all components are defined in a single script tag for browser compatibility, they are logically separated within the code:

1. **Modal** - Reusable modal dialog component
2. **Header** - Top header with project configuration
3. **ResourceList** - Left sidebar with list of API resources
4. **Editor** - Middle panel with Monaco editor for JSON editing
5. **Preview** - Right panel with OpenAPI preview
6. **NewApiModal** - Modal for creating new APIs

## Utility Functions

The application includes several utility functions:

1. **Monaco Editor Configuration** - Setup for the Monaco editor
2. **API Utilities** - Functions for interacting with the server API

## Running the Designer

To run the designer:

```bash
cd designer
python server.py
```

Then open http://localhost:8888/index.html in your browser.

## Development Notes

The application uses:

- React for UI components
- Monaco Editor for JSON editing
- Tailwind CSS for styling
- Fetch API for server communication

All components are defined in a single script tag to avoid module loading issues in the browser environment while maintaining logical separation in the code.

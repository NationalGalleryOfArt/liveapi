# LiveAPI Serverless Designer - MVP Plan

This document outlines the plan for creating a minimal, serverless API designer for the LiveAPI library. The goal is to provide a simple, visual tool for developers to design an API and see the resulting OpenAPI specification without requiring a web server or complex frontend build process.

## Core Concept: The "Command-Line Bridge"

The architecture is designed to be completely "offline." A user interacts with a static HTML file in their browser, and then uses a simple Python script to process the design and generate the specification.

- **No Web Server:** The tool does not require running a local web server.
- **No Frontend Build:** The frontend is a single HTML file that uses CDNs for React, Tailwind CSS, and Babel, eliminating the need for Node.js or npm.
- **No Core Library Changes:** The tool uses the existing `SpecGenerator` as a library without modifying its code.

## File Structure

The following new files will be created in a `designer/` directory:

```
designer/
├── designer.html           # The main React-based UI for editing the API design.
├── preview.html            # A static page to display the generated Swagger docs.
├── generate_from_json.py   # The Python script that bridges the UI and the library.
└── build/                    # Directory for generated output.
    └── openapi.json          # The generated OpenAPI specification.
```

---

## Component Breakdown

### 1. `designer/designer.html` (The UI)

This is the main user interface for designing the API.

- **Technology:**
  - **HTML:** A single static file.
  - **React/ReactDOM:** Loaded from a CDN to build the UI components.
  - **Babel (Standalone):** Loaded from a CDN to transpile JSX directly in the browser.
  - **Tailwind CSS:** Loaded from the Play CDN for styling.
- **Layout:**
  - A two-column layout using Tailwind CSS Flexbox.
  - **Left Column:** A large `<textarea>` for editing the `api_info` JSON. It will be pre-populated with a default example.
  - **Right Column:** An `<iframe>` that will load `preview.html`.
- **Functionality:**
  - The React application will manage the state of the JSON in the textarea.
  - A "Copy JSON" button will be provided for user convenience.

### 2. `designer/generate_from_json.py` (The Bridge)

This script is the core of the workflow, connecting the user's design to the `liveapi` generator.

- **Functionality:**
  1.  It will be a command-line script that accepts one argument: the path to a JSON file containing the `api_info` data.
  2.  It will read and parse the input JSON file.
  3.  It will import `SpecGenerator` from `src.liveapi.spec_generator` and `LLM` from `src.liveapi.llms.base`.
  4.  It will instantiate the generator.
  5.  It will call `spec_generator.generate_spec_with_json()` with the loaded `api_info`.
  6.  It will save the resulting OpenAPI specification to `designer/build/openapi.json`.
- **Usage:**
  ```bash
  python designer/generate_from_json.py /path/to/my_api_design.json
  ```

### 3. `designer/preview.html` (The Viewer)

A simple, static HTML file for viewing the generated documentation.

- **Technology:**
  - **Swagger UI:** The necessary CSS and JS for Swagger UI will be loaded from a CDN.
- **Functionality:**
  - On load, it will initialize Swagger UI and point it to the local `./build/openapi.json` file.
  - This provides a clean and immediate way to review the output of the generation script.

---

## User Workflow

1.  **Open Designer:** The user opens `designer/designer.html` in their web browser.
2.  **Edit Design:** The user modifies the pre-filled JSON in the left-hand textarea to define their API.
3.  **Save Design:** The user copies the JSON from the textarea and saves it to a file (e.g., `my_api.json`).
4.  **Generate Spec:** The user runs the Python script from their terminal:
    ```bash
    python designer/generate_from_json.py my_api.json
    ```
5.  **Preview Docs:** The user opens (or refreshes) `designer/preview.html` in their browser. The `<iframe>` in `designer.html` will also update if it's pointing to this file. The Swagger documentation for their newly designed API is displayed.

This plan provides a robust and minimal solution for an API designer tool that complements the existing library perfectly.

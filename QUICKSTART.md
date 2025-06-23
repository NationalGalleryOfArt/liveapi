# LiveAPI Quick Start Guide

Get up and running with LiveAPI in 5 minutes.

## Prerequisites

- Python 3.13+
- pip

## Installation

```bash
git clone <repository-url>
cd liveapi
pip install -e .
```

## 5-Minute Tutorial

### Step 1: Initialize Your Project
```bash
mkdir my-api
cd my-api
liveapi init
```

### Step 2: Generate an API Specification
You can either generate a spec interactively, or create one manually.

**Option A: Interactive Generation (Recommended)**
```bash
liveapi generate
```
Follow the interactive prompts to define your API.

**Option B: Manual Creation**
Create a file named `specifications/users.yaml` with your OpenAPI content.

### Step 3: Sync
```bash
liveapi sync
```
This will create a `main.py` file that is ready to run your API.

### Step 4: Run Your API
```bash
liveapi run
```

### Step 5: Test Your API
```bash
curl http://localhost:8000/health
# Assuming you created a 'users' API
curl http://localhost:8000/users
```

### Step 6: View Interactive Docs
Open your browser to `http://localhost:8000/docs` to see the Swagger UI.

## Making Changes

1.  **Edit your spec**: Modify your `users.yaml` file to add a new endpoint or change an existing one.
2.  **Check what changed**: Run `liveapi status` to see a summary of your changes.
3.  **Create a new version**: Run `liveapi version create --minor` to create a new, versioned spec file.
4.  **Update your application**: Run `liveapi sync` to make your running API aware of the changes.

Your API now reflects the new changes!

## Stop the Development Server

When you're done, you can stop the server with:
```bash
liveapi kill
```

## What's Next?

- Explore more commands like `liveapi version list` and `liveapi version compare`.
- Learn about the `liveapi.implementation` package to understand how the dynamic server works.

# LiveAPI Quick Start Guide

Get up and running with LiveAPI in 5 minutes!

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
You can either generate a spec with AI, or create one manually.

**Option A: AI Generation (Recommended)**
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
curl http://localhost:8000/users
```

### Step 6: View Interactive Docs
Open your browser to http://localhost:8000/docs to see the Swagger UI.

## Making Changes

### Add a New Endpoint

Edit `users.yaml` and add a new endpoint.

### Check What Changed

```bash
liveapi status
```

### Create New Version

```bash
liveapi version create --minor
```

### Update Implementation

```bash
liveapi sync
```

Your API now has the new endpoint!

### Stop Development Server

When you're done:
```bash
liveapi kill
```

## What's Next?

- Explore more commands like `liveapi version list` and `liveapi version compare`.
- Learn about the `liveapi.implementation` package to understand how the dynamic server works.

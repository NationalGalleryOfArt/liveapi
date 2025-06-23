# Refactoring Plan: A New Vision for LiveAPI

This document outlines a new, simplified architectural vision for LiveAPI and a step-by-step plan to refactor the codebase to align with this vision.

## The Core Problem: Architectural Tension

The current implementation of LiveAPI suffers from a fundamental architectural tension between two competing goals:

1.  **The `automatic` Goal:** To be a generic, real-time engine that can run *any* valid OpenAPI specification.
2.  **The `liveapi` Goal:** To provide a structured, opinionated framework for building high-quality, standardized APIs.

This conflict has led to a complex and bloated codebase that is difficult to maintain and extend.

## The New Vision: An Opinionated, Real-Time API Engine

To resolve this tension, we are adopting a new, more focused vision for LiveAPI:

**LiveAPI will be an opinionated, real-time API engine for building, versioning, and managing standardized "CRUD+" APIs.**

We will no longer attempt to be a generic OpenAPI server. Instead, we will focus on providing a powerful, streamlined experience for the most common API patterns.

### The "CRUD+" Interface

The core of this new vision is the "CRUD+" interface, a standardized set of operations that cover the vast majority of API use cases:

*   **Create:** `POST /resources`
*   **Read:** `GET /resources/{id}`
*   **Update:** `PUT /resources/{id}` or `PATCH /resources/{id}`
*   **Delete:** `DELETE /resources/{id}`
*   **List (Index):** `GET /resources`
*   **Search/Filtering:** A `List` operation with query parameters (e.g., `GET /users?status=active`).

By standardizing on this interface, we can dramatically simplify the implementation while still providing a high degree of flexibility.

### Core Technologies

*   **FastAPI:** The underlying web framework.
*   **Pydantic:** The library for all data modeling and validation. We will use Pydantic's `create_model` function for dynamic, real-time model generation.

## The Refactoring Plan

We will execute this refactoring in the following steps:

**Step 1: Create the `liveapi.implementation` Package** ✅
   - The `automatic` package will be renamed to `liveapi.implementation` to better reflect its new, more focused mission.

**Step 2: Replace `TypedDictGenerator` with Pydantic** ✅
   - The `TypedDictGenerator` class will be deleted.
   - It will be replaced with a new module that uses Pydantic's `create_model` function to dynamically generate Pydantic models from OpenAPI schemas at runtime.

**Step 3: Implement Standard "CRUD+" Handlers** ✅
   - We will create a set of standard, reusable FastAPI route handlers for each of the "CRUD+" operations.
   - These handlers will be responsible for the core logic of creating, reading, updating, deleting, and listing resources.

**Step 4: Create a "LiveAPI Spec" Parser and Router** ✅
   - We will create a new parser that is specifically designed to understand the "LiveAPI dialect" of OpenAPI.
   - This parser will identify "CRUD+" resources in a spec and map them to the standard handlers.
   - This will replace the generic routing logic in the current `automatic` package.

**Step 5: Consolidate and Simplify** ✅
   - The remaining code in the `liveapi.implementation` package will be reviewed, consolidated, and simplified.
   - Any code that is not directly related to implementing the "CRUD+" vision will be removed.

**Step 6: Update Documentation and Tests** ✅
   - All project documentation, including `CLAUDE.md` and the `README.md`, will be updated to reflect the new architecture.
   - The test suite will be updated to cover the new implementation.

**Step 7: Remove Non-CRUD Code (Aggressive Cleanup)** ✅
   - Removed all legacy code generation and scaffolding
   - Deleted base classes, request processors, validators, and response transformers
   - Eliminated templates and custom implementation support
   - Simplified to pure CRUD-only dynamic handlers

## Expected Outcomes

This refactoring will result in:

*   **A Dramatically Simplified Codebase:** We will remove hundreds of lines of complex, custom code.
*   **Improved Maintainability:** The new architecture will be easier to understand, maintain, and extend.
*   **Increased Robustness:** By relying on Pydantic and a standardized set of handlers, the system will be more reliable and less prone to errors.
*   **A Clearer Product Vision:** LiveAPI will have a clear, focused mission that is easier to communicate to users.

This plan represents a significant step forward for the LiveAPI project. It will allow us to build a more powerful, more reliable, and more valuable tool for our users.

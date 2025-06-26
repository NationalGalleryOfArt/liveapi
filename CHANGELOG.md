# Changelog

All notable changes to the LiveAPI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.0] - 2025-06-26

### 🪝 SQLModelResource Hook-Based Architecture

#### Added
- **BaseSQLModelResource**: New abstract base class containing core CRUD logic with extensible hook methods
- **Hook-Based Customization**: Developers can now customize SQLModel resource behavior without overriding entire CRUD methods
- **Data Transformation Hooks**:
  - `to_dto()`: Transform database models to API-friendly formats (e.g., field renaming, computed fields)
  - `from_api()`: Transform incoming API data to database format (e.g., field mapping, data conversion)
- **Lifecycle Hooks**:
  - `before_create()` / `after_create()`: Add validation, defaults, or trigger side effects on creation
  - `before_update()` / `after_update()`: Validate updates, track changes, or invalidate caches
  - `before_delete()` / `after_delete()`: Prevent deletion, archive records, or cascade cleanup
- **Query Customization Hook**:
  - `build_list_query()`: Add custom filters, joins, or ordering to list operations

#### Changed
- **SQLModelResource Architecture**: Complete rewrite using template method pattern with extensible hooks
- **Template Enhancement**: Updated `sql_model_resource_subclass.py.j2` template to generate resource classes with comprehensive hook examples
- **Improved Partial Updates**: Fixed handling of None values in transformations for proper PATCH support

#### Benefits
- **Cleaner Code**: Business logic separated from CRUD mechanics
- **Better Maintainability**: Override only what you need, inherit the rest
- **Production Ready**: Clear extension points for validation, logging, caching, and external integrations
- **Type Safe**: Full type hints throughout the hook system

#### Technical Details
- Created `src/liveapi/implementation/base_sql_model_resource.py` with template method pattern
- Rewrote `src/liveapi/implementation/sql_model_resource.py` to inherit from base class
- Added comprehensive test suite in `tests/test_sql_model_resource_hooks.py` with 8 test cases
- All 155 tests pass including the new hook functionality tests
- Mock-based testing approach integrates cleanly with existing test infrastructure

## [0.10.2] - 2025-06-25

### 🐛 Critical Bug Fixes - 422 Validation Error Handling

#### Fixed
- **JSON Schema Validation Constraints**: Fixed critical issue where OpenAPI validation constraints (`minLength`, `maxLength`, `minimum`, `maximum`, `pattern`, etc.) were not being enforced
- **422 Error Format Consistency**: Fixed mismatch between OpenAPI documentation and actual 422 error responses
- **RFC 7807 Compliance**: Ensured all 422 validation errors use proper RFC 7807 format with `application/problem+json` Content-Type
- **OpenAPI Schema Override**: Fixed issue where existing specs with outdated ValidationError schemas would show incorrect error format in documentation

#### Enhanced
- **PydanticGenerator**: Added `_extract_validation_constraints()` method to properly translate JSON Schema constraints to Pydantic Field constraints
- **ValidationError Schema**: Always use correct RFC 7807 format in OpenAPI spec regardless of existing schema definitions
- **Error Response Examples**: Added proper examples in OpenAPI documentation showing actual error format

#### Changed
- **Template File Naming**: Renamed template files for better clarity:
  - `sql_model_service.py.j2` → `sql_model_resource_subclass.py.j2`
  - `implementation.py.j2` → `default_resource_subclass.py.j2`
- **Documentation Updates**: Updated CLAUDE.md to reflect new template names and added missing main.py.j2

#### Technical Details
- Modified `src/liveapi/implementation/pydantic_generator.py` to extract and apply JSON Schema validation constraints
- Updated `src/liveapi/implementation/liveapi_router.py` to always ensure correct ValidationError schema in OpenAPI spec
- Updated `src/liveapi/sync/executor.py` to reference renamed template files
- Fixed typos and added missing templates in project documentation

#### Impact
- **Before**: Validation constraints in OpenAPI specs were ignored, invalid data would return 201 (success)
- **After**: Validation constraints are properly enforced, invalid data returns 422 with proper RFC 7807 error format
- **Compatibility**: No breaking changes, existing projects automatically get the fixes

## [0.10.1] - 2025-06-25

### 🎨 LiveAPI Designer - Enhanced Resource Management

#### Added
- **Resource Management UI**: Dropdown to list, select, edit, and delete existing API resources
- **Editable Project Configuration**: API name and base URL can be edited directly in the designer interface
- **Resource Persistence**: Resources are automatically saved to `.liveapi/prompts/` and can be reloaded
- **Enhanced UX**: Workflow text updated to "Edit JSON → Preview API Spec → Confirm API"
- **No Auto-Generation**: Removed automatic preview generation on page load

#### Fixed
- **Preview Refresh Issue**: Fixed race condition where preview wouldn't update after generation
- **Cache-Busting Support**: Fixed query parameter handling in API endpoints (`/api/openapi.json?t=...`)
- **Memory Caching**: Added in-memory caching for generated OpenAPI specs to eliminate file system timing issues
- **File System Synchronization**: Added proper file flushing and sync to ensure file writes complete before serving

#### Changed
- **Button Renaming**: "Scaffold Application" renamed to "Confirm API" for clarity
- **Removed Refresh Button**: Preview automatically refreshes when spec is generated
- **Enhanced Logging**: Improved debug logging for troubleshooting preview issues
- **Project Storage**: OpenAPI specs now stored in project's `.liveapi/openapi.json` instead of library directory

#### Technical Implementation
- **Dual Serving Strategy**: Serves OpenAPI specs from memory cache first, then falls back to file system
- **Path Matching Fix**: Enhanced URL pattern matching to handle cache-busting query parameters
- **Resource API Endpoints**: Added `/api/resources`, `/api/resource/{name}`, and DELETE support
- **Configuration Endpoints**: Added `/api/config` for reading/writing project configuration
- **Improved Error Handling**: Better error messages and fallback behavior for missing resources

## [0.10.0] - 2025-06-24

### 🎨 LiveAPI Designer - Visual API Design Tool

#### Added
- **LiveAPI Designer**: A browser-based visual tool for designing APIs
- **New CLI Command**: `liveapi designer` to launch the designer UI
- **Serverless Architecture**: No build process or complex setup required
- **Real-time Preview**: See OpenAPI documentation as you design
- **Auto-refresh**: Preview automatically updates when changes are made
- **JSON Editor**: Simple JSON-based API design interface
- **Example APIs**: Pre-configured example API designs
- **Root Redirection**: Automatic redirection to designer.html from root URL

#### Technical Implementation
- **Static HTML Interface**: Single-page React application loaded from CDN
- **Python HTTP Server**: Simple server for static files and API generation
- **OpenAPI Generation**: Uses existing SpecGenerator for consistency
- **Browser Integration**: Automatic browser opening with webbrowser module
- **Port Configuration**: Configurable port with `--port` option (default: 8888)

#### Documentation
- **Designer README**: Comprehensive documentation in designer/README.md
- **Updated Main README**: Added designer command to command reference
- **Example JSON Files**: Included example API designs for quick start

#### Benefits
- **Visual Design**: Easier API design for visual thinkers
- **No Dependencies**: Works without Node.js, npm, or complex build tools
- **Immediate Feedback**: See changes to your API in real-time
- **Simplified Workflow**: Design → Generate → Preview in one interface

## [0.9.0] - 2025-06-23

### 🗃️ Database Integration - Pluggable Backend Architecture

#### Added
- **Pluggable Service Layer**: Choose between multiple data persistence backends during API generation
- **SQLModelResourceService**: Production-ready SQL database backend using SQLModel ORM
- **Interactive Backend Selection**: Choose backend during `liveapi generate` with automatic configuration saving
- **Database Connection Management**: Complete SQLModel setup with connection pooling and session management
- **Automatic Table Creation**: SQLModel tables auto-generated from OpenAPI schemas with proper types
- **Configuration Persistence**: Backend choice saved to `.liveapi/config.json` and used across sessions
- **Graceful Fallback**: Automatic fallback to DefaultResourceService if SQLModel dependencies unavailable

#### Enhanced
- **PydanticGenerator**: Now supports both Pydantic BaseModel and SQLModel table generation based on backend
- **LiveAPIRouter**: Backend-aware service instantiation based on project configuration
- **Interactive Workflow**: Added backend selection step with clear options for prototyping vs production
- **Project Metadata**: Enhanced ProjectConfig model to include backend_type field

#### Technical Implementation
- **DatabaseManager**: Centralized database connection and session management
- **SQLModelResourceService**: Full CRUD operations with proper SQL queries, filtering, and transactions
- **Backend Detection**: Automatic configuration loading from project metadata
- **Model Generation**: Conditional SQLModel table creation with primary keys and relationships
- **Template System**: Jinja2 templates for generating database configuration and service files

#### Testing & Documentation
- **Comprehensive Test Suite**: 20 test cases covering all database integration scenarios
- **DATABASE_SETUP.md**: Complete setup guide for SQL backends with PostgreSQL and SQLite examples
- **Updated CLAUDE.md**: Enhanced documentation with database backend workflows and examples
- **Environment Configuration**: Support for DATABASE_URL and DATABASE_DEBUG environment variables

#### Database Features
- **Multi-Database Support**: PostgreSQL (production) and SQLite (development) with automatic detection
- **Query Filtering**: Advanced filtering with exact match, comparisons, and text search
- **Transaction Safety**: Proper rollback handling and error management
- **Timestamp Management**: Automatic created_at and updated_at field handling
- **UUID Generation**: Automatic ID generation for new records

#### Migration
- Existing projects continue working with DefaultResourceService (in-memory)
- New projects can choose SQL backend during generation
- No breaking changes to existing functionality
- Configuration automatically migrated when regenerating APIs

### Benefits
- **Production Ready**: SQL database persistence for real applications
- **Development Friendly**: In-memory option remains for rapid prototyping
- **Future Extensible**: Architecture ready for Redis, Elasticsearch, and other backends
- **Configuration Managed**: User choice persists across all LiveAPI operations
- **Zero Lock-in**: Easy switching between backends during development

## [0.8.0] - 2025-06-23

### Refactoring
- Renamed `CRUDHandlers` to `DefaultResourceService` to better reflect its purpose as a default, in-memory implementation.
- Renamed `create_crud_router` to `create_resource_router`.
- Updated all internal references and documentation to use the new names.

## [0.7.0] - 2025-06-23

### 🧹 Code Cleanup and Simplification

#### Changed
- **Removed Vestigial CRUD Logic**: Removed all remaining conditional logic related to the old "CRUD vs. non-CRUD" distinction. The entire system now assumes a consistent CRUD-based architecture.
- **Simplified `liveapi_parser.py`**: The `identify_crud_resources` method is now much simpler, as it no longer needs to categorize operations.
- **Simplified `generator.py`**: Removed the old logic for generating specs from natural language descriptions and simplified the `generate_spec_with_json` method.
- **Simplified CLI**: Removed the `--crud` flag from the `sync` command, as it is no longer needed.
- **Simplified `executor.py`**: Removed the `_execute_crud_mode` function and simplified the `execute_sync_plan` function.

#### Fixed
- **End-to-End Tests**: Fixed the failing end-to-end tests by restoring the `_categorize_operation` method and the logic in `identify_crud_resources` to populate the `operations` dictionary.

## [0.6.0] - 2025-06-23

### 🏗️ Implementation Generation Overhaul - Database-Ready Service Classes

#### Added
- **Database-Ready Implementation Generation**: `liveapi sync` now generates customizable service classes by default
- **CRUD Method Overrides**: Individual async methods (`create_resource`, `get_resource`, `list_resources`, `update_resource`, `delete_resource`) for database integration
- **Database Integration Points**: Clear TODOs and examples for connecting PostgreSQL, MongoDB, or any database
- **Business Logic Hooks**: Built-in spots for validation, logging, caching, and event publishing
- **Professional Error Handling**: RFC 7807 compliant error responses with proper exception handling examples
- **Auto-Discovery Main App**: Generated `main.py` automatically loads and mounts custom service implementations
- **Dual Mode Support**: `--crud` flag available for legacy dynamic CRUD+ behavior

#### Changed
- **Default Sync Behavior**: `liveapi sync` now generates `implementations/` directory with service classes
- **Project Structure**: Added `implementations/` directory to standard project layout
- **Service Architecture**: Moved from pure dynamic handlers to customizable class-based approach
- **Error Handling**: Enhanced with ValidationError, ConflictError, and HTTPException examples
- **Documentation**: Updated README, ARCHITECTURE, and examples to reflect new approach

#### Technical Details
- Modified `src/liveapi/sync/executor.py` to generate implementation files by default
- Added comprehensive error handling examples in generated service classes
- Updated CLI help text and argument handling for new `--crud` flag
- Enhanced documentation with database integration examples
- Maintained backward compatibility with existing CRUD+ infrastructure

#### Migration
- Existing projects: Run `liveapi sync` to generate new implementation files
- Legacy behavior: Use `liveapi sync --crud` for old dynamic mode
- No breaking changes to existing functionality

### Benefits
- **Production Ready**: Generated code ready for real database connections
- **Clear Extension Points**: Obvious places to add business logic and database calls
- **Professional Error Handling**: Industry-standard error responses and exception management
- **Maintainable Architecture**: Service classes that can be version controlled and customized

## [0.5.0] - 2025-06-23

### 🎨 Major UX Improvements - Interactive Workflow Overhaul

#### Added
- **Streamlined Interactive Workflow**: Object-first approach eliminates duplicate questions
- **Smart Auto-Inference**: API name/description automatically suggested from resource information
- **JSON Array Examples**: Clean format for providing multiple example objects in a single input
- **Professional FastAPI Implementation**: Proper parameter naming and schema handling
- **RFC 7807 Validation Errors**: Industry-standard error format with correct Content-Type headers

#### Changed
- **Interactive Prompts**: Reordered workflow to ask for object name first, then auto-infer API details
- **Parameter Naming**: Fixed DELETE/PUT/PATCH endpoints to use 'id' instead of 'resource_id'
- **Request/Response Schemas**: Use typed Pydantic models instead of generic objects
- **List Responses**: Return proper array types instead of string responses
- **Examples Integration**: Examples from user input now appear correctly in Swagger documentation
- **Project Name Inference**: Auto-generate project name from resource name (no duplicate prompts)
- **Base URL Handling**: Automatically use existing project configuration when available

#### Fixed
- **Duplicate Questions**: Eliminated asking for project name and base URL multiple times
- **FastAPI Parameter Issues**: All endpoints now use correct parameter names and types
- **Swagger Documentation**: Examples provided by users now display properly in API docs
- **Validation Error Format**: Professional RFC 7807 compliant error responses with proper headers
- **Test Compatibility**: Updated all 67 tests to work with improved workflow

#### Technical Details
- Modified `src/liveapi/generator/interactive.py` to implement object-first workflow
- Updated `src/liveapi/implementation/liveapi_router.py` with RFC 7807 error handling
- Fixed parameter extraction in `src/liveapi/generator/generator.py` to use integer types for 'id'
- Enhanced Pydantic model generation with example support
- Updated all test files to match new workflow expectations

### Migration
- Existing projects continue to work without changes
- New interactive workflow provides better UX for new API generation
- All existing prompts and schemas remain compatible

## [0.4.0] - 2025-06-23

### Changed
- **Authentication Simplified**: Removed API key authentication from the core system - now handled at API Gateway level
- **CRUD-Only Focus**: Simplified codebase by removing conditional CRUD detection logic since all APIs are now CRUD-based
- **Test Reliability**: Fixed cloud development environment test issues by eliminating authentication complexity
- **No Pagination**: Simplified list endpoints to return arrays instead of pagination objects for easier integration

### Removed
- **API Key Authentication**: Removed `verify_api_key`, `get_api_key_dependency`, and related auth logic
- **Auth Files**: Deleted `src/liveapi/implementation/auth.py` and `examples/api_key_demo.py`
- **CRUD Detection**: Removed `_is_crud_scenario()` and `_is_crud_resource()` methods - all resources are treated as CRUD
- **Pagination Complexity**: Removed pagination wrappers from list responses

### Fixed
- **End-to-End Tests**: All tests now pass (67 passed, 0 failed) including complete workflow validation
- **Cloud Environment Compatibility**: Tests work reliably in cloud dev environments with URL forwarding
- **Test Naming**: Renamed `test_api_key_authentication` to `test_basic_api_functionality`

## [0.3.0] - 2025-06-22

### Changed
- **Major Refactoring**: Replaced the `automatic` code generation package with a new, dynamic `liveapi.implementation` engine.
- **CRUD+ Runtime**: APIs are now served dynamically from OpenAPI specifications using a standardized set of CRUD+ handlers. No code is generated for implementations.
- **Pydantic Integration**: Replaced custom `TypedDict` generation with dynamic Pydantic model creation.
- **Simplified `sync` command**: The `liveapi sync` command no longer generates implementation files. It now creates a simple `main.py` file that runs the dynamic API server.

### Removed
- **Code Generation**: Removed the entire `automatic` package and all related code generation logic.

## [0.2.0] - 2025-06-22

### Changed

#### 🔄 Simplified Spec Generator
- **Removed LLM dependency**: No longer requires OpenRouter API or API keys
- **Structured CRUD approach**: Direct generation of CRUD APIs with JSON schema input
- **Simplified workflow**: More predictable and consistent output
- **Faster generation**: No waiting for API responses
- **Improved developer experience**: Direct control over generated specs

### Technical Improvements
- **Removed API key handling**: Simplified codebase with no external API dependencies
- **Streamlined interactive flow**: Focused questions for CRUD API generation
- **Maintained schema editing**: Still supports editing JSON schemas for regeneration
- **Backward compatible**: Existing prompts and schemas still work

### Migration
- No migration needed - existing projects continue to work
- API keys are no longer required
- OPENROUTER_MODEL environment variable is no longer used

## [0.1.0] - 2025-06-20

### 🚀 Major CLI Rewrite - Zero Configuration OpenAPI Framework

Significant improvements to the CLI for maximum simplicity and developer productivity.

### Added

#### 🚀 Zero-Configuration Auto-Discovery
- **Ultimate simplicity**: Just run `automatic` in any directory with OpenAPI specs
- **Smart project detection**: Automatically detects first-run vs incremental mode
- **Multi-spec support**: Processes all `.yaml`, `.yml`, and `.json` files automatically
- **Complete project setup**: Creates `specifications/`, `implementations/`, `main.py`, and `.gitignore`

#### 🏗️ Rails-Style Base Classes
- **BaseCrudImplementation**: Automatic CRUD operation delegation for REST APIs
- **BaseImplementation**: Helper methods for custom business logic
- **Intelligent selection**: Auto-detects CRUD vs custom patterns and chooses appropriate base class

#### 🧠 Smart Code Generation
- **Meaningful class names**: `users.yaml` → `UserService`, `products_v2.yaml` → `ProductsV2Service`
- **Custom validation hooks**: Override `validate_create()`, `validate_update()`, etc.
- **Resource building**: Customize resource creation with `build_resource()`
- **Method delegation**: OpenAPI operations automatically delegate to CRUD methods

#### 🔐 Built-in Authentication
- **API Key authentication**: Header-based `X-API-Key` support with metadata
- **Bearer token authentication**: Standard `Authorization: Bearer` support
- **Flexible configuration**: Lists, dicts, environment variables, single values
- **Auth context**: Authentication info passed to all implementation methods

#### 🛡️ Comprehensive Error Handling
- **Business exceptions**: `NotFoundError`, `ValidationError`, `ConflictError`, etc.
- **RFC 7807 compliance**: Standardized error response format
- **Automatic mapping**: Business exceptions → appropriate HTTP status codes
- **Context preservation**: Include additional data in error responses

#### 🏥 Built-in Health Monitoring
- **Automatic `/health` endpoint**: Added to every application
- **Timestamp tracking**: ISO-formatted current time in responses
- **Service identification**: Includes service name for monitoring

### Changed

#### 🎛️ Complete CLI Redesign
- **BREAKING**: Removed `automatic scaffold` subcommand
- **BREAKING**: Renamed `api/` directory to `specifications/`
- **Simplified**: Single `automatic` command with auto-discovery
- **Removed flags**: No more `--init`, `--no-init`, `-f` flags
- **User-friendly**: Asks for permission before overwriting files

#### 📁 Directory Structure
- **BREAKING**: Default spec directory changed from `api/` to `specifications/`
- **Organized**: Clear separation of specs and implementations
- **Automatic**: Directory creation during first run

### Technical Improvements

#### 🧪 Comprehensive Testing
- **Auto-discovery tests**: Complete test coverage for all discovery modes
- **Multi-spec testing**: End-to-end testing with multiple API specifications
- **Edge case handling**: Empty directories, invalid specs, overwrite scenarios

#### 🔧 Enhanced CLI Architecture
- **Mode detection**: Automatic first-run vs incremental mode detection
- **Batch processing**: Efficient handling of multiple specifications
- **Error recovery**: Graceful handling of invalid or missing files

#### 📚 Documentation
- **Complete rewrite**: Updated all documentation for v1.0 patterns
- **Examples**: Working examples for all major use cases
- **Migration guide**: Clear guidance for upgrading from development versions

### Migration from Development Versions

If you were using development versions of automatic:

1. **Directory rename**: Move `api/` directory to `specifications/`
2. **CLI change**: Replace `automatic scaffold` with just `automatic`
3. **No breaking changes**: Existing implementation files work without modification

### Examples

#### Zero-Configuration Setup
```bash
# Place your OpenAPI specs in any directory
ls *.yaml
# users.yaml  orders.yaml  products.yaml

# One command setup
automatic
# ✅ Complete project structure created
# ✅ All implementations generated with proper base classes
# ✅ main.py configured and ready to run
```

#### Generated CRUD Implementation
```python
class UserService(BaseCrudImplementation):
    resource_name = "user"
    
    def get_data_store(self) -> Dict[str, Any]:
        return self._data_store
    
    def get_user(self, data):
        return self.show(data.get('user_id'), auth_info=data.get('auth'))
    
    def create_user(self, data):
        return self.create(data=data.get('body', {}), auth_info=data.get('auth'))
```

### Current Feature Set

✅ **Rails-style CRUD base classes** with automatic method delegation  
✅ **Zero-configuration auto-discovery** for seamless multi-API projects  
✅ **Intelligent project setup** with pattern detection and smart class naming  
✅ **Built-in authentication** (API Key & Bearer Token)  
✅ **Comprehensive error handling** with RFC 7807 compliance
✅ **Built-in health monitoring** with automatic `/health` endpoint  
✅ **Dynamic FastAPI route generation** from OpenAPI specifications  
✅ **Request validation** with Pydantic models  
✅ **Multi-API support** with automatic discovery  
✅ **Version-aware routing** (v1, v2, etc.)  
✅ **Working examples** demonstrating all features  
✅ **Comprehensive test coverage**

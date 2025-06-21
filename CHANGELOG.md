# Changelog

All notable changes to the automatic project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **RFC 9457 compliance**: Standardized error response format
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
✅ **Comprehensive error handling** with RFC 9457 compliance  
✅ **Built-in health monitoring** with automatic `/health` endpoint  
✅ **Dynamic FastAPI route generation** from OpenAPI specifications  
✅ **Request validation** with Pydantic models  
✅ **Multi-API support** with automatic discovery  
✅ **Version-aware routing** (v1, v2, etc.)  
✅ **Working examples** demonstrating all features  
✅ **Comprehensive test coverage**
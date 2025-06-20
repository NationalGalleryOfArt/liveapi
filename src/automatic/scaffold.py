"""Scaffold generation for automatic implementations."""

import sys
from pathlib import Path
from typing import Dict, List, Any, Set
from .parser import OpenAPIParser


class ScaffoldGenerator:
    """Generates implementation scaffolds from OpenAPI specifications."""
    
    def __init__(self, spec_path: str):
        self.spec_path = Path(spec_path)
        self.parser = OpenAPIParser(spec_path)
        
    def generate_scaffold(self, output_path: str, force: bool = False):
        """Generate scaffold implementation file."""
        output_file = Path(output_path)
        
        # Check if file exists and handle overwrite
        if output_file.exists() and not force:
            response = input(f"⚠️  File '{output_path}' already exists. Overwrite? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("❌ Scaffold generation cancelled.")
                return
        
        # Parse the OpenAPI spec
        routes = self.parser.get_routes()
        
        # Generate implementation code
        code = self._generate_implementation_code(routes)
        
        # Write to file
        output_file.write_text(code)
        
    def _generate_implementation_code(self, routes: List[Dict[str, Any]]) -> str:
        """Generate the implementation class code."""
        # Get unique operation IDs
        operation_ids = [route['operation_id'] for route in routes]
        
        # Generate imports
        imports = self._generate_imports()
        
        # Generate class definition
        class_def = self._generate_class_definition()
        
        # Generate methods
        methods = []
        for route in routes:
            method_code = self._generate_method(route)
            methods.append(method_code)
        
        # Combine all parts
        code_parts = [
            imports,
            "",
            class_def,
            ""
        ]
        
        for method in methods:
            code_parts.extend([method, ""])
        
        return "\n".join(code_parts)
    
    def _generate_imports(self) -> str:
        """Generate import statements."""
        return '''"""Implementation for OpenAPI specification."""

import json
from typing import Dict, Any, Tuple
from automatic import (
    NotFoundError,
    ValidationError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError,
    ServiceUnavailableError
)'''
    
    def _generate_class_definition(self) -> str:
        """Generate class definition."""
        class_name = self._get_class_name()
        return f'''class {class_name}:
    """Implementation class for OpenAPI operations."""
    
    def __init__(self):
        """Initialize the implementation."""
        pass'''
    
    def _generate_method(self, route: Dict[str, Any]) -> str:
        """Generate method implementation."""
        operation_id = route['operation_id']
        method = route['method']
        path = route['path']
        summary = route.get('summary', '')
        description = route.get('description', '')
        
        # Extract expected status codes from responses
        responses = route.get('responses', {})
        success_codes = [code for code in responses.keys() if code.startswith('2')]
        error_codes = [code for code in responses.keys() if not code.startswith('2')]
        
        # Generate method signature and docstring
        method_code = f'''    def {operation_id}(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        {summary}
        
        {description}
        
        Method: {method}
        Path: {path}
        
        Args:
            data: Request data containing:
                - Path parameters (if any)
                - Query parameters (if any) 
                - Request body (if any)
                - Authentication info in data['auth'] (if configured)
        
        Returns:
            Tuple of (response_data, status_code)
        
        Raises:'''
        
        # Add exception documentation
        exception_docs = self._generate_exception_docs(error_codes)
        method_code += exception_docs
        
        method_code += f'''
        """
        print(f"🔄 {operation_id} called with data: {{json.dumps(data, indent=2)}}")
        
        # TODO: Implement your business logic here
        # 
        # Example patterns:
        #
        # 1. Access path parameters:
        #    user_id = data.get('user_id')
        #
        # 2. Access query parameters:
        #    limit = data.get('limit', 10)
        #
        # 3. Access request body:
        #    body = data.get('body', {{}})
        #
        # 4. Access authentication info:
        #    auth_info = data.get('auth')
        #    if not auth_info:
        #        raise UnauthorizedError("Authentication required")
        #
        # 5. Validate input:
        #    if not data.get('required_field'):
        #        raise ValidationError("Required field missing")
        #
        # 6. Handle not found:
        #    if resource_id not in self.resources:
        #        raise NotFoundError(f"Resource {{resource_id}} not found")
        #
        # 7. Handle conflicts:
        #    if self.resource_exists(data['name']):
        #        raise ConflictError("Resource already exists")
        
        # Placeholder response
        response_data = {{
            "message": "Not implemented yet",
            "operation": "{operation_id}",
            "method": "{method}",
            "path": "{path}",
            "received_data": data
        }}
        
        # Return successful response (change status code as needed)'''
        
        # Add default success status code
        if success_codes:
            default_status = success_codes[0]
        else:
            default_status = "200"
            
        method_code += f'''
        return response_data, {default_status}'''
        
        return method_code
    
    def _generate_exception_docs(self, error_codes: List[str]) -> str:
        """Generate exception documentation based on error codes."""
        exceptions = []
        
        for code in error_codes:
            if code == '400':
                exceptions.append("            ValidationError: For invalid input (400)")
            elif code == '401':
                exceptions.append("            UnauthorizedError: For authentication required (401)")
            elif code == '403':
                exceptions.append("            ForbiddenError: For insufficient permissions (403)")
            elif code == '404':
                exceptions.append("            NotFoundError: For resource not found (404)")
            elif code == '409':
                exceptions.append("            ConflictError: For resource conflicts (409)")
            elif code == '429':
                exceptions.append("            RateLimitError: For rate limit exceeded (429)")
            elif code == '503':
                exceptions.append("            ServiceUnavailableError: For service unavailable (503)")
        
        if exceptions:
            return "\n" + "\n".join(exceptions)
        else:
            return "\n            BusinessException: For any business logic errors"
    
    def _get_class_name(self) -> str:
        """Generate class name from spec file name."""
        stem = self.spec_path.stem
        
        # Convert to PascalCase without removing version info
        # example.yaml -> ExampleImplementation
        # users_v2.yaml -> UsersV2Implementation  
        words = stem.replace('-', '_').split('_')
        class_name = ''.join(word.capitalize() for word in words if word)
        
        return f"{class_name}Implementation"
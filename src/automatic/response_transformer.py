"""Response transformation utilities for RFC 9457 error handling."""

from typing import Any, Dict, Union


class ResponseTransformer:
    """Transforms responses to standardized formats, particularly RFC 9457 for errors."""
    
    def transform_response(self, data: Any, status_code: int) -> Any:
        """Transform response data based on status code."""
        if self.is_error_status(status_code):
            return self.transform_error(data, status_code)
        return data
    
    def transform_error(self, error_data: Union[str, Dict], status_code: int) -> Dict[str, Any]:
        """Transform error data to RFC 9457 Problem Details format."""
        if isinstance(error_data, str):
            return self._string_to_rfc9457(error_data, status_code)
        elif isinstance(error_data, dict):
            return self._enhance_dict_to_rfc9457(error_data, status_code)
        else:
            return self._string_to_rfc9457(str(error_data), status_code)
    
    def is_error_status(self, status_code: int) -> bool:
        """Check if status code represents an error (4xx or 5xx)."""
        return status_code >= 400
    
    def _string_to_rfc9457(self, message: str, status_code: int) -> Dict[str, Any]:
        """Convert simple string error to RFC 9457 format."""
        return {
            "type": "about:blank",
            "title": message,
            "status": status_code
        }
    
    def _enhance_dict_to_rfc9457(self, error_dict: Dict, status_code: int) -> Dict[str, Any]:
        """Enhance dict error to RFC 9457 format if missing required fields."""
        # If already RFC 9457 compliant (has type, title, status), return as-is
        if all(key in error_dict for key in ["type", "title", "status"]):
            return error_dict
        
        # Create RFC 9457 structure, preserving original fields
        result = dict(error_dict)  # Copy original fields
        
        # Add missing RFC 9457 fields
        if "type" not in result:
            result["type"] = "about:blank"
        
        if "title" not in result:
            # Try to extract title from common error fields
            title = (result.get("message") or 
                    result.get("error") or 
                    result.get("detail") or 
                    "An error occurred")
            result["title"] = title
        
        if "status" not in result:
            result["status"] = status_code
        
        return result
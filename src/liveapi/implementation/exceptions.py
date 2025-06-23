"""Business exceptions that map to HTTP status codes."""

from typing import Optional, Dict, Any


class BusinessException(Exception):
    """Base exception for business logic errors that map to HTTP responses."""

    status_code: int = 400
    error_type: str = "business_error"

    def __init__(self, detail: str, extra: Optional[Dict[str, Any]] = None):
        self.detail = detail
        self.extra = extra or {}
        super().__init__(detail)

    def to_response(self) -> Dict[str, Any]:
        """Convert to RFC 7807 error response."""
        return {
            "type": f"/errors/{self.error_type}",
            "title": self.__class__.__name__.replace("Error", ""),
            "status": self.status_code,
            "detail": self.detail,
            **self.extra,
        }


class ValidationError(BusinessException):
    """Invalid input data."""

    status_code = 400
    error_type = "validation_error"


class NotFoundError(BusinessException):
    """Resource not found."""

    status_code = 404
    error_type = "not_found"


class ConflictError(BusinessException):
    """Resource conflict (e.g., duplicate)."""

    status_code = 409
    error_type = "conflict"


class UnauthorizedError(BusinessException):
    """Authentication required."""

    status_code = 401
    error_type = "unauthorized"


class ForbiddenError(BusinessException):
    """Insufficient permissions."""

    status_code = 403
    error_type = "forbidden"

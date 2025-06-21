"""Middleware for automatic framework."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from starlette.requests import Request


class RedirectSlashesMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle trailing slash redirects.
    
    Redirects URLs with trailing slashes to their non-trailing slash equivalents,
    except for the root path "/".
    
    Examples:
        /locations/ -> /locations (301 redirect)
        /users/123/ -> /users/123 (301 redirect)
        / -> / (no redirect)
    """
    
    async def dispatch(self, request: Request, call_next):
        """Handle the request and redirect if needed."""
        path = request.url.path
        
        # Don't redirect root path or paths that don't end with slash
        if path == "/" or not path.endswith("/"):
            return await call_next(request)
        
        # Remove trailing slash and redirect
        new_path = path.rstrip("/")
        
        # Preserve query parameters
        query_string = str(request.url.query)
        new_url = str(request.url.replace(path=new_path, query=query_string))
        
        return RedirectResponse(url=new_url, status_code=301)
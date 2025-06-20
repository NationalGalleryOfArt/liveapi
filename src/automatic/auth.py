"""Authentication module for automatic framework."""

from typing import Optional, Dict, Any, List, Union, Callable
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
import os
from .exceptions import UnauthorizedError


class APIKeyAuth:
    """API Key authentication handler."""
    
    def __init__(
        self,
        api_keys: Union[List[str], Dict[str, Any], str, None] = None,
        header_name: str = "X-API-Key",
        auto_error: bool = True,
        env_var: str = "API_KEY"
    ):
        """
        Initialize API Key authentication.
        
        Args:
            api_keys: Valid API keys. Can be:
                - List of strings: ['key1', 'key2']
                - Dict mapping keys to metadata: {'key1': {'name': 'admin'}}
                - Single string: 'single_key'
                - None: Will use env_var
            header_name: Header name for API key (default: X-API-Key)
            auto_error: Whether to automatically raise HTTP 401 on auth failure
            env_var: Environment variable name if api_keys is None
        """
        self.auto_error = auto_error
        self.env_var = env_var
        
        # Normalize api_keys to dict format
        if api_keys is None:
            # Try to get from environment variable
            env_key = os.getenv(env_var)
            if env_key:
                self.api_keys = {env_key: {"source": "environment"}}
            else:
                self.api_keys = {}
        elif isinstance(api_keys, str):
            self.api_keys = {api_keys: {"source": "direct"}}
        elif isinstance(api_keys, list):
            self.api_keys = {key: {"source": "list"} for key in api_keys}
        elif isinstance(api_keys, dict):
            self.api_keys = api_keys
        else:
            raise ValueError("api_keys must be None, str, list, or dict")
        
        # Create FastAPI security scheme
        self.header_scheme = APIKeyHeader(name=header_name, auto_error=False)
    
    def __call__(self) -> Callable:
        """Return the dependency function for FastAPI."""
        async def dependency(
            api_key: Optional[str] = Depends(self.header_scheme),
        ) -> Optional[Dict[str, Any]]:
            """
            Validate API key from header.
            
            Returns:
                Dict with key metadata if valid, None if invalid and auto_error=False
                
            Raises:
                HTTPException: If key is invalid and auto_error=True
            """
            
            if not api_key:
                if self.auto_error:
                    raise HTTPException(status_code=401, detail={
                        "type": "/errors/unauthorized",
                        "title": "Unauthorized",
                        "status": 401,
                        "detail": "API key required"
                    })
                return None
            
            if api_key in self.api_keys:
                return {
                    "api_key": api_key,
                    "metadata": self.api_keys[api_key]
                }
            
            if self.auto_error:
                raise HTTPException(status_code=401, detail={
                    "type": "/errors/unauthorized",
                    "title": "Unauthorized", 
                    "status": 401,
                    "detail": "Invalid API key"
                })
            return None
        
        return dependency


class BearerTokenAuth:
    """Bearer token authentication handler."""
    
    def __init__(
        self,
        tokens: Union[List[str], Dict[str, Any], str, None] = None,
        auto_error: bool = True,
        env_var: str = "BEARER_TOKEN"
    ):
        """
        Initialize Bearer token authentication.
        
        Args:
            tokens: Valid bearer tokens. Can be:
                - List of strings: ['token1', 'token2']
                - Dict mapping tokens to metadata: {'token1': {'user': 'admin'}}
                - Single string: 'single_token'
                - None: Will use env_var
            auto_error: Whether to automatically raise HTTP 401 on auth failure
            env_var: Environment variable name if tokens is None
        """
        self.auto_error = auto_error
        self.env_var = env_var
        
        # Normalize tokens to dict format
        if tokens is None:
            env_token = os.getenv(env_var)
            if env_token:
                self.tokens = {env_token: {"source": "environment"}}
            else:
                self.tokens = {}
        elif isinstance(tokens, str):
            self.tokens = {tokens: {"source": "direct"}}
        elif isinstance(tokens, list):
            self.tokens = {token: {"source": "list"} for token in tokens}
        elif isinstance(tokens, dict):
            self.tokens = tokens
        else:
            raise ValueError("tokens must be None, str, list, or dict")
        
        self.bearer_scheme = HTTPBearer(auto_error=False)
    
    def __call__(self) -> Callable:
        """Return the dependency function for FastAPI."""
        async def dependency(
            credentials: Optional[HTTPAuthorizationCredentials] = Depends(self.bearer_scheme)
        ) -> Optional[Dict[str, Any]]:
            """
            Validate bearer token.
            
            Returns:
                Dict with token metadata if valid, None if invalid and auto_error=False
                
            Raises:
                HTTPException: If token is invalid and auto_error=True
            """
            if not credentials:
                if self.auto_error:
                    raise HTTPException(status_code=401, detail={
                        "type": "/errors/unauthorized",
                        "title": "Unauthorized",
                        "status": 401,
                        "detail": "Bearer token required"
                    })
                return None
            
            token = credentials.credentials
            
            if token in self.tokens:
                return {
                    "token": token,
                    "metadata": self.tokens[token]
                }
            
            if self.auto_error:
                raise HTTPException(status_code=401, detail={
                    "type": "/errors/unauthorized",
                    "title": "Unauthorized",
                    "status": 401,
                    "detail": "Invalid bearer token"
                })
            return None
        
        return dependency


# Convenience functions for common auth patterns
def create_api_key_auth(
    api_keys: Union[List[str], Dict[str, Any], str, None] = None,
    **kwargs
) -> APIKeyAuth:
    """Create API key authentication dependency."""
    return APIKeyAuth(api_keys=api_keys, **kwargs)


def create_bearer_auth(
    tokens: Union[List[str], Dict[str, Any], str, None] = None,
    **kwargs
) -> BearerTokenAuth:
    """Create Bearer token authentication dependency."""
    return BearerTokenAuth(tokens=tokens, **kwargs)
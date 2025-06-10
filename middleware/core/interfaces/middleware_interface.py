"""
Interface untuk middleware components.
Mengikuti prinsip Interface Segregation Principle (ISP).
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Protocol
from fastapi import Request, Response


class MiddlewareInterface(Protocol):
    """
    Interface untuk middleware components.
    """
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """Process incoming request."""
        ...
    
    async def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """Process outgoing response."""
        ...


class AuthenticationInterface(Protocol):
    """
    Interface untuk authentication middleware.
    """
    
    async def authenticate(self, request: Request) -> bool:
        """Authenticate request."""
        ...
    
    async def get_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get authenticated user."""
        ...


class AuthorizationInterface(Protocol):
    """
    Interface untuk authorization middleware.
    """
    
    async def authorize(self, request: Request, resource: str, action: str) -> bool:
        """Authorize request for resource and action."""
        ...
    
    async def check_permission(self, user: Dict[str, Any], permission: str) -> bool:
        """Check user permission."""
        ...


class CacheInterface(Protocol):
    """
    Interface untuk cache middleware.
    """
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value to cache."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        ...


class RateLimitInterface(Protocol):
    """
    Interface untuk rate limiting middleware.
    """
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        ...
    
    async def get_remaining(self, identifier: str) -> int:
        """Get remaining requests."""
        ...


class LoggingInterface(Protocol):
    """
    Interface untuk logging middleware.
    """
    
    async def log_request(self, request: Request) -> None:
        """Log incoming request."""
        ...
    
    async def log_response(self, request: Request, response: Response) -> None:
        """Log outgoing response."""
        ...


class MonitoringInterface(Protocol):
    """
    Interface untuk monitoring middleware.
    """
    
    async def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record metric."""
        ...
    
    async def start_trace(self, operation: str) -> str:
        """Start tracing operation."""
        ...
    
    async def end_trace(self, trace_id: str) -> None:
        """End tracing operation."""
        ...


class SecurityInterface(Protocol):
    """
    Interface untuk security middleware.
    """
    
    async def validate_request(self, request: Request) -> bool:
        """Validate request security."""
        ...
    
    async def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data."""
        ...

"""
Interface untuk handler components.
Mengikuti prinsip Interface Segregation Principle (ISP).
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Union, Protocol
from fastapi import Request, Response


class HandlerInterface(Protocol):
    """
    Interface untuk handler components.
    """
    
    async def handle(self, request: Request, **kwargs) -> Union[Request, Response, Any]:
        """Handle request."""
        ...
    
    def can_handle(self, request: Request, **kwargs) -> bool:
        """Check if can handle request."""
        ...


class ErrorHandlerInterface(Protocol):
    """
    Interface untuk error handler.
    """
    
    async def handle_error(self, request: Request, error: Exception) -> Response:
        """Handle error and return response."""
        ...
    
    def can_handle_error(self, error: Exception) -> bool:
        """Check if can handle this error type."""
        ...


class RequestHandlerInterface(Protocol):
    """
    Interface untuk request handler.
    """
    
    async def process_request(self, request: Request) -> Request:
        """Process incoming request."""
        ...
    
    async def validate_request(self, request: Request) -> bool:
        """Validate request."""
        ...


class ResponseHandlerInterface(Protocol):
    """
    Interface untuk response handler.
    """
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """Process outgoing response."""
        ...
    
    async def format_response(self, data: Any) -> Dict[str, Any]:
        """Format response data."""
        ...


class AuthHandlerInterface(Protocol):
    """
    Interface untuk authentication handler.
    """
    
    async def authenticate_user(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate user with credentials."""
        ...
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate authentication token."""
        ...
    
    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh authentication token."""
        ...


class ValidationHandlerInterface(Protocol):
    """
    Interface untuk validation handler.
    """
    
    async def validate_data(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Validate data against schema."""
        ...
    
    async def sanitize_data(self, data: Any) -> Any:
        """Sanitize input data."""
        ...


class CacheHandlerInterface(Protocol):
    """
    Interface untuk cache handler.
    """
    
    async def get_cached_response(self, key: str) -> Optional[Response]:
        """Get cached response."""
        ...
    
    async def cache_response(self, key: str, response: Response, ttl: Optional[int] = None) -> bool:
        """Cache response."""
        ...
    
    async def invalidate_cache(self, pattern: str) -> bool:
        """Invalidate cache by pattern."""
        ...


class SecurityHandlerInterface(Protocol):
    """
    Interface untuk security handler.
    """
    
    async def check_security_headers(self, request: Request) -> bool:
        """Check security headers."""
        ...
    
    async def detect_threats(self, request: Request) -> bool:
        """Detect security threats."""
        ...
    
    async def apply_security_policies(self, request: Request) -> Request:
        """Apply security policies."""
        ...


class MonitoringHandlerInterface(Protocol):
    """
    Interface untuk monitoring handler.
    """
    
    async def track_request(self, request: Request) -> str:
        """Track request and return tracking ID."""
        ...
    
    async def record_metrics(self, request: Request, response: Response, duration: float) -> None:
        """Record request metrics."""
        ...
    
    async def send_alerts(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Send monitoring alerts."""
        ...

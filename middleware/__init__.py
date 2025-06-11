"""
Middleware package initialization.
Menyediakan easy import untuk semua middleware components.
"""

# Core components
from .core.abstract.base_middleware import BaseMiddleware
from .core.abstract.base_handler import BaseHandler
from .core.registry.middleware_registry import middleware_registry, MiddlewareRegistry
from .core.registry.dependency_container import dependency_container, DependencyContainer
from .core.interfaces.middleware_interface import (
    MiddlewareInterface,
    AuthenticationInterface,
    AuthorizationInterface,
    CacheInterface,
    RateLimitInterface,
    LoggingInterface,
    MonitoringInterface,
    SecurityInterface
)

# Authentication middleware
from .authentication.auth_middleware import AuthMiddleware
from .authentication.auth.jwt_middleware import JWTMiddleware, JWTAuthStrategy
from .authentication.interfaces.auth_strategy import AuthStrategy, TokenData, AuthenticatedUser

# Security middleware
from .security.cors_middleware import CORSMiddleware

# Performance middleware
from .performance.rate_limiter import RateLimitMiddleware, TokenBucketRateLimiter, SlidingWindowRateLimiter
from .performance.cache_middleware import CacheMiddleware, InMemoryCache

# Logging middleware
from .logging.request_logger import RequestLoggerMiddleware

# Error handling middleware
from .error.exception_handler import (
    ExceptionHandlerMiddleware,
    CustomException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    BusinessLogicException
)

# Setup functions
from .setup import (
    initialize_middleware,
    setup_middleware_registry,
    setup_auth_strategies,
    get_middleware_stack,
    get_middleware_by_group
)

__version__ = "1.0.0"

__all__ = [
    # Core
    "BaseMiddleware",
    "BaseHandler",
    "middleware_registry",
    "MiddlewareRegistry",
    "dependency_container",
    "DependencyContainer",
    
    # Interfaces
    "MiddlewareInterface",
    "AuthenticationInterface",
    "AuthorizationInterface",
    "CacheInterface",
    "RateLimitInterface",
    "LoggingInterface",
    "MonitoringInterface",
    "SecurityInterface",
    
    # Authentication
    "AuthMiddleware",
    "JWTMiddleware",
    "JWTAuthStrategy",
    "AuthStrategy",
    "TokenData",
    "AuthenticatedUser",
    
    # Security
    "CORSMiddleware",
    
    # Performance
    "RateLimitMiddleware",
    "TokenBucketRateLimiter",
    "SlidingWindowRateLimiter",
    "CacheMiddleware",
    "InMemoryCache",
    
    # Logging
    "RequestLoggerMiddleware",
    
    # Error Handling
    "ExceptionHandlerMiddleware",
    "CustomException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "NotFoundException",
    "BusinessLogicException",
    
    # Setup
    "initialize_middleware",
    "setup_middleware_registry",
    "setup_auth_strategies",
    "get_middleware_stack",
    "get_middleware_by_group",
]


def get_version():
    """Get middleware package version."""
    return __version__


def list_available_middleware():
    """List all available middleware."""
    return {
        "authentication": ["JWTMiddleware", "AuthMiddleware"],
        "security": ["CORSMiddleware"],
        "performance": ["RateLimitMiddleware", "CacheMiddleware"],
        "logging": ["RequestLoggerMiddleware"],
        "error": ["ExceptionHandlerMiddleware"]
    }


def create_middleware_stack(config=None):
    """
    Create and return configured middleware stack.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        List of configured middleware instances
    """
    if config:
        # Apply custom configuration
        for name, middleware_config in config.items():
            if middleware_registry.is_registered(name):
                middleware_registry.update_config(name, middleware_config)
    
    return get_middleware_stack()

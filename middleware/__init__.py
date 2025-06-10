"""
Middleware package untuk aplikasi.
Menyediakan berbagai middleware components yang mengikuti prinsip SOLID dan DRY.
"""
from .core import (
    BaseMiddleware,
    BaseHandler,
    BaseValidator,
    ValidationResult,
    MiddlewareRegistry,
    middleware_registry,
    DependencyContainer,
    dependency_container
)
from .authentication import AuthMiddleware, AuthStrategy

__version__ = "1.0.0"

__all__ = [
    # Core Components
    'BaseMiddleware',
    'BaseHandler',
    'BaseValidator',
    'ValidationResult',
    'MiddlewareRegistry',
    'middleware_registry',
    'DependencyContainer',
    'dependency_container',
    
    # Authentication
    'AuthMiddleware',
    'AuthStrategy'
]

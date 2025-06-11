"""
Middleware setup dan registrasi.
Mengatur semua middleware yang tersedia dalam aplikasi.
"""
from middleware.core.registry.middleware_registry import middleware_registry
from middleware.core.registry.dependency_container import dependency_container

# Import semua middleware
from middleware.authentication.auth_middleware import AuthMiddleware
from middleware.authentication.auth.jwt_middleware import JWTMiddleware
from middleware.security.cors_middleware import CORSMiddleware
from middleware.performance.rate_limiter import RateLimitMiddleware
from middleware.performance.cache_middleware import CacheMiddleware
from middleware.logging.request_logger import RequestLoggerMiddleware
from middleware.error.exception_handler import ExceptionHandlerMiddleware


def setup_middleware_registry():
    """
    Setup dan register semua middleware ke registry.
    """
    
    # Exception Handler Middleware (highest priority)
    middleware_registry.register(
        name='exception_handler',
        middleware_class=ExceptionHandlerMiddleware,
        config={
            'debug_mode': False,
            'log_exceptions': True
        },
        group='error',
        priority=1
    )
    
    # CORS Middleware (very high priority)
    middleware_registry.register(
        name='cors',
        middleware_class=CORSMiddleware,
        config={
            'allowed_origins': ['*'],
            'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allowed_headers': ['*'],
            'allow_credentials': True,
            'max_age': 600
        },
        group='security',
        priority=5
    )
    
    # Request Logger Middleware
    middleware_registry.register(
        name='request_logger',
        middleware_class=RequestLoggerMiddleware,
        config={
            'log_requests': True,
            'log_responses': True,
            'log_headers': False,
            'log_body': False,
            'excluded_paths': ['/health', '/metrics', '/docs', '/redoc']
        },
        group='logging',
        priority=8
    )
    
    # Authentication Middleware
    middleware_registry.register(
        name='jwt_auth',
        middleware_class=JWTMiddleware,
        config={
            'secret_key': 'your-jwt-secret-key',
            'algorithm': 'HS256',
            'expire_minutes': 30,
            'public_paths': ['/auth/login', '/auth/register', '/docs', '/redoc', '/openapi.json', '/health']
        },
        group='authentication',
        priority=10
    )
    
    # Rate Limiting Middleware
    middleware_registry.register(
        name='rate_limit',
        middleware_class=RateLimitMiddleware,
        config={
            'algorithm': 'token_bucket',
            'capacity': 100,
            'refill_rate': 10.0,
            'excluded_paths': ['/health', '/metrics', '/docs', '/redoc']
        },
        group='performance',
        priority=20
    )
    
    # Cache Middleware
    middleware_registry.register(
        name='cache',
        middleware_class=CacheMiddleware,
        config={
            'backend': 'memory',
            'default_ttl': 300,
            'excluded_paths': ['/auth/*', '/admin/*', '/docs', '/redoc'],
            'endpoint_ttls': {
                '/api/products': 600,
                '/api/categories': 1800
            }
        },
        group='performance',
        priority=30
    )


def setup_auth_strategies():
    """
    Setup authentication strategies dalam dependency container.
    """
    from middleware.authentication.auth.jwt_middleware import JWTAuthStrategy
    
    # JWT Strategy
    jwt_strategy = JWTAuthStrategy(
        secret_key='your-jwt-secret-key',
        algorithm='HS256',
        expire_minutes=30
    )
    dependency_container.register_service('auth_strategy_jwt', jwt_strategy)
    
    # API Key Strategy (akan diimplementasi nanti)
    # from middleware.authentication.strategies.api_key_strategy import APIKeyAuthStrategy
    # api_key_strategy = APIKeyAuthStrategy()
    # dependency_container.register_service('auth_strategy_api_key', api_key_strategy)


def get_middleware_stack():
    """
    Get ordered middleware stack untuk aplikasi.
    
    Returns:
        List middleware instances dalam urutan priority
    """
    return middleware_registry.get_all_ordered()


def get_middleware_by_group(group: str):
    """
    Get middleware berdasarkan group.
    
    Args:
        group: Nama group (authentication, security, performance, etc.)
        
    Returns:
        List middleware instances dalam group
    """
    return middleware_registry.get_by_group(group)


# Initialize middleware setup
def initialize_middleware():
    """Initialize semua middleware dan dependencies."""
    setup_auth_strategies()
    setup_middleware_registry()
    
    print("✅ Middleware registry initialized")
    print(f"📋 Registered middleware: {middleware_registry.list_registered()}")
    print(f"🏷️  Available groups: {middleware_registry.list_groups()}")

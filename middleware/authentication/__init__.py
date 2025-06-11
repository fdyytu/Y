"""
Authentication middleware package.
Menyediakan berbagai strategi autentikasi dan middleware terkait.
"""

# Core authentication middleware
from .middleware.auth_middleware import AuthenticationMiddleware

# Authentication strategies
from .interfaces.auth_strategy import AuthStrategy, TokenData, AuthenticatedUser
from .strategies.jwt_strategy import JWTStrategy
from .strategies.api_key_strategy import APIKeyStrategy
from .strategies.oauth2_strategy import OAuth2Strategy

# Authentication providers
from .providers.google_provider import GoogleProvider
from .providers.facebook_provider import FacebookProvider
from .providers.apple_provider import AppleProvider

# Authentication services
from .services.auth_service import AuthService
from .services.token_service import TokenService
from .services.session_service import SessionService
from .services.refresh_service import RefreshService
from .services.user_service import UserService

# Specific auth middleware
from .auth.jwt_middleware import JWTMiddleware
from .auth.api_key_middleware import APIKeyMiddleware
from .auth.oauth_middleware import OAuthMiddleware
from .auth.role_middleware import RoleMiddleware

__version__ = "1.0.0"

__all__ = [
    # Core
    'AuthenticationMiddleware',
    
    # Interfaces & Strategies
    'AuthStrategy',
    'TokenData',
    'AuthenticatedUser',
    'JWTStrategy',
    'APIKeyStrategy',
    'OAuth2Strategy',
    
    # Providers
    'GoogleProvider',
    'FacebookProvider',
    'AppleProvider',
    
    # Services
    'AuthService',
    'TokenService',
    'SessionService',
    'RefreshService',
    'UserService',
    
    # Specific Middleware
    'JWTMiddleware',
    'APIKeyMiddleware',
    'OAuthMiddleware',
    'RoleMiddleware',
]


def get_available_strategies():
    """Mendapatkan daftar strategi autentikasi yang tersedia."""
    return {
        'jwt': JWTStrategy,
        'api_key': APIKeyStrategy,
        'oauth2': OAuth2Strategy,
    }


def get_available_providers():
    """Mendapatkan daftar provider OAuth yang tersedia."""
    return {
        'google': GoogleProvider,
        'facebook': FacebookProvider,
        'apple': AppleProvider,
    }


def get_available_services():
    """Mendapatkan daftar service yang tersedia."""
    return {
        'auth': AuthService,
        'token': TokenService,
        'session': SessionService,
        'refresh': RefreshService,
        'user': UserService,
    }


def get_available_middleware():
    """Mendapatkan daftar middleware yang tersedia."""
    return {
        'auth': AuthenticationMiddleware,
        'jwt': JWTMiddleware,
        'api_key': APIKeyMiddleware,
        'oauth': OAuthMiddleware,
        'role': RoleMiddleware,
    }


def create_auth_middleware(strategy_type='jwt', **kwargs):
    """
    Factory function untuk membuat authentication middleware.
    
    Args:
        strategy_type: Tipe strategi ('jwt', 'api_key', 'oauth2')
        **kwargs: Konfigurasi tambahan
        
    Returns:
        Instance dari authentication middleware
    """
    strategies = get_available_strategies()
    
    if strategy_type not in strategies:
        raise ValueError(f"Strategy '{strategy_type}' tidak tersedia. "
                        f"Pilihan: {list(strategies.keys())}")
    
    strategy = strategies[strategy_type](**kwargs)
    return AuthenticationMiddleware(strategy=strategy)


def create_auth_service(config=None):
    """
    Factory function untuk membuat authentication service.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Instance dari AuthService
    """
    return AuthService(config)


def create_provider(provider_type, config):
    """
    Factory function untuk membuat OAuth provider.
    
    Args:
        provider_type: Tipe provider ('google', 'facebook', 'apple')
        config: Provider configuration
        
    Returns:
        Instance dari provider
        
    Raises:
        ValueError: Jika provider_type tidak didukung
    """
    providers = get_available_providers()
    
    if provider_type not in providers:
        raise ValueError(f"Provider '{provider_type}' tidak tersedia. "
                        f"Pilihan: {list(providers.keys())}")
    
    return providers[provider_type](config)


def create_strategy(strategy_type, config=None):
    """
    Factory function untuk membuat authentication strategy.
    
    Args:
        strategy_type: Tipe strategy ('jwt', 'api_key', 'oauth2')
        config: Strategy configuration
        
    Returns:
        Instance dari strategy
        
    Raises:
        ValueError: Jika strategy_type tidak didukung
    """
    strategies = get_available_strategies()
    
    if strategy_type not in strategies:
        raise ValueError(f"Strategy '{strategy_type}' tidak tersedia. "
                        f"Pilihan: {list(strategies.keys())}")
    
    if config:
        return strategies[strategy_type](config)
    else:
        return strategies[strategy_type]()


def create_service(service_type, config=None):
    """
    Factory function untuk membuat service.
    
    Args:
        service_type: Tipe service ('auth', 'token', 'session', 'refresh', 'user')
        config: Service configuration
        
    Returns:
        Instance dari service
        
    Raises:
        ValueError: Jika service_type tidak didukung
    """
    services = get_available_services()
    
    if service_type not in services:
        raise ValueError(f"Service '{service_type}' tidak tersedia. "
                        f"Pilihan: {list(services.keys())}")
    
    return services[service_type](config)


def get_package_info():
    """Mendapatkan informasi lengkap tentang package."""
    return {
        'name': 'Authentication Middleware',
        'version': __version__,
        'description': 'Comprehensive authentication middleware package',
        'strategies': list(get_available_strategies().keys()),
        'providers': list(get_available_providers().keys()),
        'services': list(get_available_services().keys()),
        'middleware': list(get_available_middleware().keys()),
        'features': [
            'JWT Authentication',
            'API Key Authentication', 
            'OAuth 2.0 Support',
            'Role-based Access Control',
            'Session Management',
            'Token Management',
            'Multi-provider OAuth',
            'Refresh Token Rotation',
            'Rate Limiting',
            'Security Middleware'
        ]
    }


# Convenience imports untuk backward compatibility
AuthMiddleware = AuthenticationMiddleware

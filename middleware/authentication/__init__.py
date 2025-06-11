"""
Authentication middleware package.
Menyediakan berbagai strategi autentikasi dan middleware terkait.
"""

# Core authentication middleware
from .auth_middleware import AuthMiddleware
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
from .services.token_service import TokenService
from .services.session_service import SessionService
from .services.refresh_service import RefreshService

# Specific auth middleware
from .auth.jwt_middleware import JWTMiddleware
from .auth.api_key_middleware import APIKeyMiddleware
from .auth.oauth_middleware import OAuthMiddleware
from .auth.role_middleware import RoleMiddleware

__version__ = "1.0.0"

__all__ = [
    # Core
    'AuthMiddleware',
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
    'TokenService',
    'SessionService',
    'RefreshService',
    
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
    return AuthMiddleware(strategy=strategy)

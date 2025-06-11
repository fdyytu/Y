"""
Authentication middleware implementations.
Berisi implementasi konkret dari berbagai middleware autentikasi.
"""

# JWT Authentication
from .jwt_middleware import JWTMiddleware, JWTAuthStrategy

# API Key Authentication
from .api_key_middleware import APIKeyMiddleware, APIKeyAuthStrategy

# OAuth Authentication
from .oauth_middleware import OAuthMiddleware, OAuthAuthStrategy

# Role-based Authentication
from .role_middleware import RoleMiddleware, RoleAuthStrategy

__version__ = "1.0.0"

__all__ = [
    # JWT
    'JWTMiddleware',
    'JWTAuthStrategy',
    
    # API Key
    'APIKeyMiddleware',
    'APIKeyAuthStrategy',
    
    # OAuth
    'OAuthMiddleware',
    'OAuthAuthStrategy',
    
    # Role-based
    'RoleMiddleware',
    'RoleAuthStrategy',
]


def get_auth_middleware_types():
    """Mendapatkan daftar tipe middleware autentikasi yang tersedia."""
    return {
        'jwt': JWTMiddleware,
        'api_key': APIKeyMiddleware,
        'oauth': OAuthMiddleware,
        'role': RoleMiddleware,
    }


def create_auth_middleware(auth_type='jwt', **config):
    """
    Factory function untuk membuat middleware autentikasi.
    
    Args:
        auth_type: Tipe autentikasi ('jwt', 'api_key', 'oauth', 'role')
        **config: Konfigurasi middleware
        
    Returns:
        Instance middleware autentikasi
    """
    middleware_types = get_auth_middleware_types()
    
    if auth_type not in middleware_types:
        raise ValueError(f"Auth type '{auth_type}' tidak tersedia. "
                        f"Pilihan: {list(middleware_types.keys())}")
    
    return middleware_types[auth_type](**config)

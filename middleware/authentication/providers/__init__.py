"""
Authentication providers package.
Berisi implementasi berbagai OAuth dan authentication providers.
"""

# OAuth Providers
from .google_provider import GoogleProvider
from .facebook_provider import FacebookProvider
from .apple_provider import AppleProvider

__version__ = "1.0.0"

__all__ = [
    'GoogleProvider',
    'FacebookProvider', 
    'AppleProvider',
]


def get_available_providers():
    """Mendapatkan daftar provider yang tersedia."""
    return {
        'google': GoogleProvider,
        'facebook': FacebookProvider,
        'apple': AppleProvider,
    }


def create_provider(provider_type: str, config: dict):
    """
    Factory function untuk membuat provider instance.
    
    Args:
        provider_type: Tipe provider ('google', 'facebook', 'apple')
        config: Konfigurasi provider
        
    Returns:
        Instance provider
        
    Raises:
        ValueError: Jika provider_type tidak didukung
    """
    providers = get_available_providers()
    
    if provider_type not in providers:
        raise ValueError(f"Provider '{provider_type}' tidak tersedia. "
                        f"Pilihan: {list(providers.keys())}")
    
    return providers[provider_type](config)


def get_provider_info():
    """Mendapatkan informasi tentang semua provider."""
    return {
        'google': {
            'name': 'Google OAuth 2.0',
            'description': 'Google OAuth 2.0 authentication provider',
            'scopes': ['openid', 'email', 'profile'],
            'auth_url': 'https://accounts.google.com/o/oauth2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo'
        },
        'facebook': {
            'name': 'Facebook Login',
            'description': 'Facebook OAuth 2.0 authentication provider',
            'scopes': ['email', 'public_profile'],
            'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
            'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
            'user_info_url': 'https://graph.facebook.com/me'
        },
        'apple': {
            'name': 'Sign in with Apple',
            'description': 'Apple ID authentication provider',
            'scopes': ['name', 'email'],
            'auth_url': 'https://appleid.apple.com/auth/authorize',
            'token_url': 'https://appleid.apple.com/auth/token',
            'user_info_url': 'https://appleid.apple.com/auth/userinfo'
        }
    }

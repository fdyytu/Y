"""
Authentication services package.
Berisi berbagai service untuk authentication dan token management.
"""

# Core services
from .token_service import TokenService
from .session_service import SessionService
from .refresh_service import RefreshService

# Authentication services
from .auth_service import AuthService
from .user_service import UserService

__version__ = "1.0.0"

__all__ = [
    # Core Services
    'TokenService',
    'SessionService', 
    'RefreshService',
    
    # Authentication Services
    'AuthService',
    'UserService',
]


def get_available_services():
    """Mendapatkan daftar service yang tersedia."""
    return {
        'token': TokenService,
        'session': SessionService,
        'refresh': RefreshService,
        'auth': AuthService,
        'user': UserService,
    }


def create_service(service_type: str, config: dict = None):
    """
    Factory function untuk membuat service instance.
    
    Args:
        service_type: Tipe service ('token', 'session', 'refresh', 'auth', 'user')
        config: Konfigurasi service
        
    Returns:
        Instance service
        
    Raises:
        ValueError: Jika service_type tidak didukung
    """
    services = get_available_services()
    
    if service_type not in services:
        raise ValueError(f"Service '{service_type}' tidak tersedia. "
                        f"Pilihan: {list(services.keys())}")
    
    service_class = services[service_type]
    
    if config:
        return service_class(config)
    else:
        return service_class()


def get_service_info():
    """Mendapatkan informasi tentang semua service."""
    return {
        'token': {
            'name': 'Token Service',
            'description': 'Service untuk token generation, validation, dan management',
            'features': ['JWT tokens', 'Token validation', 'Token refresh', 'Token blacklist']
        },
        'session': {
            'name': 'Session Service', 
            'description': 'Service untuk session management',
            'features': ['Session creation', 'Session validation', 'Session cleanup', 'Multi-device sessions']
        },
        'refresh': {
            'name': 'Refresh Service',
            'description': 'Service untuk refresh token management',
            'features': ['Refresh token generation', 'Token rotation', 'Refresh validation', 'Cleanup expired tokens']
        },
        'auth': {
            'name': 'Authentication Service',
            'description': 'Core authentication service',
            'features': ['User authentication', 'Strategy management', 'Login/logout', 'Multi-factor auth']
        },
        'user': {
            'name': 'User Service',
            'description': 'Service untuk user management dalam context authentication',
            'features': ['User lookup', 'Role management', 'Permission checking', 'User validation']
        }
    }

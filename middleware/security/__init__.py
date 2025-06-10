"""
Security middleware package.
"""
from .cors_middleware import CORSMiddleware
from .xss_middleware import XSSMiddleware

__all__ = [
    'CORSMiddleware',
    'XSSMiddleware'
]

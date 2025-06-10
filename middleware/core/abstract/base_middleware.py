"""
Base middleware abstract class untuk semua middleware.
Mengikuti prinsip SOLID dan DRY.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from fastapi import Request, Response


class BaseMiddleware(ABC):
    """
    Abstract base class untuk semua middleware.
    Mengimplementasikan template method pattern.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize middleware dengan konfigurasi.
        
        Args:
            config: Dictionary konfigurasi middleware
        """
        self.config = config or {}
        self.setup()
    
    def setup(self) -> None:
        """
        Setup middleware. Override jika diperlukan.
        """
        pass
    
    @abstractmethod
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process incoming request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Modified request atau None jika request ditolak
            
        Raises:
            MiddlewareException: Jika terjadi error dalam processing
        """
        pass
    
    async def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """
        Process outgoing response. Override jika diperlukan.
        
        Args:
            request: FastAPI Request object
            response: FastAPI Response object
            
        Returns:
            Modified response atau None
        """
        return response
    
    async def handle_exception(self, request: Request, exc: Exception) -> Optional[Response]:
        """
        Handle exception yang terjadi dalam middleware.
        Override jika diperlukan custom exception handling.
        
        Args:
            request: FastAPI Request object
            exc: Exception yang terjadi
            
        Returns:
            Response untuk exception atau None untuk re-raise
        """
        return None
    
    def is_enabled(self) -> bool:
        """
        Check apakah middleware enabled.
        
        Returns:
            True jika middleware enabled
        """
        return self.config.get('enabled', True)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value jika key tidak ada
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)

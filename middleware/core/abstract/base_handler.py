"""
Base handler abstract class untuk semua handler middleware.
Mengikuti prinsip SOLID dan DRY.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Union
from fastapi import Request, Response
import logging


class BaseHandler(ABC):
    """
    Abstract base class untuk semua handler.
    Mengimplementasikan chain of responsibility pattern.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize handler dengan konfigurasi.
        
        Args:
            config: Dictionary konfigurasi handler
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._next_handler: Optional['BaseHandler'] = None
        self.setup()
    
    def setup(self) -> None:
        """
        Setup handler. Override jika diperlukan.
        """
        pass
    
    def set_next(self, handler: 'BaseHandler') -> 'BaseHandler':
        """
        Set next handler dalam chain.
        
        Args:
            handler: Handler selanjutnya
            
        Returns:
            Handler yang di-set sebagai next
        """
        self._next_handler = handler
        return handler
    
    @abstractmethod
    async def handle(self, request: Request, **kwargs) -> Union[Request, Response, Any]:
        """
        Handle request. Implementasi utama handler.
        
        Args:
            request: FastAPI Request object
            **kwargs: Additional arguments
            
        Returns:
            Processed request, response, atau data lainnya
            
        Raises:
            HandlerException: Jika terjadi error dalam handling
        """
        pass
    
    async def handle_next(self, request: Request, **kwargs) -> Union[Request, Response, Any]:
        """
        Pass handling ke next handler dalam chain.
        
        Args:
            request: FastAPI Request object
            **kwargs: Additional arguments
            
        Returns:
            Result dari next handler atau None jika tidak ada
        """
        if self._next_handler:
            return await self._next_handler.handle(request, **kwargs)
        return None
    
    def can_handle(self, request: Request, **kwargs) -> bool:
        """
        Check apakah handler bisa menangani request ini.
        Override jika diperlukan logic khusus.
        
        Args:
            request: FastAPI Request object
            **kwargs: Additional arguments
            
        Returns:
            True jika bisa handle request
        """
        return True
    
    def is_enabled(self) -> bool:
        """
        Check apakah handler enabled.
        
        Returns:
            True jika handler enabled
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
    
    def log_info(self, message: str, **kwargs) -> None:
        """
        Log info message.
        
        Args:
            message: Log message
            **kwargs: Additional log data
        """
        self.logger.info(message, extra=kwargs)
    
    def log_error(self, message: str, exc: Optional[Exception] = None, **kwargs) -> None:
        """
        Log error message.
        
        Args:
            message: Log message
            exc: Exception object
            **kwargs: Additional log data
        """
        self.logger.error(message, exc_info=exc, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """
        Log warning message.
        
        Args:
            message: Log message
            **kwargs: Additional log data
        """
        self.logger.warning(message, extra=kwargs)

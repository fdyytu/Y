"""
Registry untuk mengelola middleware components.
Mengimplementasikan Registry Pattern dan Dependency Injection.
"""
from typing import Dict, List, Any, Optional, Type, Callable
from abc import ABC
import logging
from ..abstract.base_middleware import BaseMiddleware
from ..interfaces.middleware_interface import MiddlewareInterface


class MiddlewareRegistry:
    """
    Registry untuk mengelola dan mengorganisir middleware.
    Mengimplementasikan Singleton pattern.
    """
    
    _instance: Optional['MiddlewareRegistry'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'MiddlewareRegistry':
        """Singleton implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize registry."""
        if not self._initialized:
            self._middlewares: Dict[str, Type[BaseMiddleware]] = {}
            self._instances: Dict[str, BaseMiddleware] = {}
            self._middleware_order: List[str] = []
            self._middleware_groups: Dict[str, List[str]] = {}
            self._middleware_configs: Dict[str, Dict[str, Any]] = {}
            self.logger = logging.getLogger(self.__class__.__name__)
            self._initialized = True
    
    def register(
        self, 
        name: str, 
        middleware_class: Type[BaseMiddleware], 
        config: Optional[Dict[str, Any]] = None,
        group: Optional[str] = None,
        priority: int = 100
    ) -> None:
        """
        Register middleware class.
        
        Args:
            name: Nama unik middleware
            middleware_class: Class middleware yang akan diregister
            config: Konfigurasi middleware
            group: Group middleware (auth, security, etc.)
            priority: Priority untuk ordering (lower = higher priority)
        """
        if not issubclass(middleware_class, BaseMiddleware):
            raise ValueError(f"Middleware {name} must inherit from BaseMiddleware")
        
        self._middlewares[name] = middleware_class
        self._middleware_configs[name] = config or {}
        
        # Add to group
        if group:
            if group not in self._middleware_groups:
                self._middleware_groups[group] = []
            self._middleware_groups[group].append(name)
        
        # Insert in order based on priority
        self._insert_by_priority(name, priority)
        
        self.logger.info(f"Registered middleware: {name} in group: {group}")
    
    def _insert_by_priority(self, name: str, priority: int) -> None:
        """Insert middleware in order based on priority."""
        # Remove if already exists
        if name in self._middleware_order:
            self._middleware_order.remove(name)
        
        # Find insertion point
        inserted = False
        for i, existing_name in enumerate(self._middleware_order):
            existing_priority = self._middleware_configs.get(existing_name, {}).get('priority', 100)
            if priority < existing_priority:
                self._middleware_order.insert(i, name)
                inserted = True
                break
        
        if not inserted:
            self._middleware_order.append(name)
    
    def get(self, name: str) -> Optional[BaseMiddleware]:
        """
        Get middleware instance by name.
        
        Args:
            name: Nama middleware
            
        Returns:
            Instance middleware atau None jika tidak ditemukan
        """
        if name not in self._middlewares:
            return None
        
        # Create instance if not exists
        if name not in self._instances:
            middleware_class = self._middlewares[name]
            config = self._middleware_configs.get(name, {})
            self._instances[name] = middleware_class(config)
        
        return self._instances[name]
    
    def get_by_group(self, group: str) -> List[BaseMiddleware]:
        """
        Get all middleware instances in a group.
        
        Args:
            group: Nama group
            
        Returns:
            List middleware instances
        """
        if group not in self._middleware_groups:
            return []
        
        middlewares = []
        for name in self._middleware_groups[group]:
            middleware = self.get(name)
            if middleware and middleware.is_enabled():
                middlewares.append(middleware)
        
        return middlewares
    
    def get_all_ordered(self) -> List[BaseMiddleware]:
        """
        Get all enabled middleware instances in priority order.
        
        Returns:
            List middleware instances dalam urutan priority
        """
        middlewares = []
        for name in self._middleware_order:
            middleware = self.get(name)
            if middleware and middleware.is_enabled():
                middlewares.append(middleware)
        
        return middlewares
    
    def unregister(self, name: str) -> bool:
        """
        Unregister middleware.
        
        Args:
            name: Nama middleware
            
        Returns:
            True jika berhasil unregister
        """
        if name not in self._middlewares:
            return False
        
        # Remove from all structures
        del self._middlewares[name]
        if name in self._instances:
            del self._instances[name]
        if name in self._middleware_order:
            self._middleware_order.remove(name)
        if name in self._middleware_configs:
            del self._middleware_configs[name]
        
        # Remove from groups
        for group_middlewares in self._middleware_groups.values():
            if name in group_middlewares:
                group_middlewares.remove(name)
        
        self.logger.info(f"Unregistered middleware: {name}")
        return True
    
    def is_registered(self, name: str) -> bool:
        """
        Check if middleware is registered.
        
        Args:
            name: Nama middleware
            
        Returns:
            True jika middleware terdaftar
        """
        return name in self._middlewares
    
    def list_registered(self) -> List[str]:
        """
        Get list of all registered middleware names.
        
        Returns:
            List nama middleware yang terdaftar
        """
        return list(self._middlewares.keys())
    
    def list_groups(self) -> List[str]:
        """
        Get list of all middleware groups.
        
        Returns:
            List nama group
        """
        return list(self._middleware_groups.keys())
    
    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get middleware configuration.
        
        Args:
            name: Nama middleware
            
        Returns:
            Configuration dictionary atau None
        """
        return self._middleware_configs.get(name)
    
    def update_config(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Update middleware configuration.
        
        Args:
            name: Nama middleware
            config: New configuration
            
        Returns:
            True jika berhasil update
        """
        if name not in self._middlewares:
            return False
        
        self._middleware_configs[name] = config
        
        # Recreate instance if exists
        if name in self._instances:
            del self._instances[name]
        
        return True
    
    def clear(self) -> None:
        """Clear all registered middleware."""
        self._middlewares.clear()
        self._instances.clear()
        self._middleware_order.clear()
        self._middleware_groups.clear()
        self._middleware_configs.clear()
        self.logger.info("Cleared all registered middleware")


# Global registry instance
middleware_registry = MiddlewareRegistry()

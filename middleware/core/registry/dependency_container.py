"""
Dependency container untuk middleware components.
Mengimplementasikan Dependency Injection Pattern.
"""
from typing import Dict, Any, Optional, Type, TypeVar, Generic, Callable
import logging
from abc import ABC, abstractmethod


T = TypeVar('T')


class DependencyContainer:
    """
    Container untuk mengelola dependencies middleware.
    Mengimplementasikan Dependency Injection dan Service Locator pattern.
    """
    
    def __init__(self):
        """Initialize dependency container."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._configurations: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_service(self, name: str, service: Any) -> None:
        """
        Register service instance.
        
        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service
        self.logger.info(f"Registered service: {name}")
    
    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register service factory.
        
        Args:
            name: Service name
            factory: Factory function yang mengembalikan service instance
        """
        self._factories[name] = factory
        self.logger.info(f"Registered factory: {name}")
    
    def register_singleton(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register singleton service.
        
        Args:
            name: Service name
            factory: Factory function untuk singleton
        """
        self._factories[name] = factory
        self.logger.info(f"Registered singleton: {name}")
    
    def register_configuration(self, name: str, config: Dict[str, Any]) -> None:
        """
        Register configuration for service.
        
        Args:
            name: Service name
            config: Configuration dictionary
        """
        self._configurations[name] = config
        self.logger.info(f"Registered configuration: {name}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Get service by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance atau None jika tidak ditemukan
        """
        # Check direct services first
        if name in self._services:
            return self._services[name]
        
        # Check singletons
        if name in self._singletons:
            return self._singletons[name]
        
        # Check factories
        if name in self._factories:
            # Create singleton if not exists
            if name not in self._singletons:
                self._singletons[name] = self._factories[name]()
            return self._singletons[name]
        
        self.logger.warning(f"Service not found: {name}")
        return None
    
    def get_new_instance(self, name: str) -> Optional[Any]:
        """
        Get new instance from factory (tidak singleton).
        
        Args:
            name: Service name
            
        Returns:
            New service instance atau None
        """
        if name in self._factories:
            return self._factories[name]()
        
        self.logger.warning(f"Factory not found: {name}")
        return None
    
    def get_configuration(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for service.
        
        Args:
            name: Service name
            
        Returns:
            Configuration dictionary atau None
        """
        return self._configurations.get(name)
    
    def has_service(self, name: str) -> bool:
        """
        Check if service is registered.
        
        Args:
            name: Service name
            
        Returns:
            True jika service terdaftar
        """
        return (name in self._services or 
                name in self._factories or 
                name in self._singletons)
    
    def remove_service(self, name: str) -> bool:
        """
        Remove service from container.
        
        Args:
            name: Service name
            
        Returns:
            True jika berhasil remove
        """
        removed = False
        
        if name in self._services:
            del self._services[name]
            removed = True
        
        if name in self._factories:
            del self._factories[name]
            removed = True
        
        if name in self._singletons:
            del self._singletons[name]
            removed = True
        
        if name in self._configurations:
            del self._configurations[name]
        
        if removed:
            self.logger.info(f"Removed service: {name}")
        
        return removed
    
    def list_services(self) -> Dict[str, str]:
        """
        List all registered services.
        
        Returns:
            Dictionary dengan service name dan type
        """
        services = {}
        
        for name in self._services:
            services[name] = "instance"
        
        for name in self._factories:
            if name in self._singletons:
                services[name] = "singleton"
            else:
                services[name] = "factory"
        
        return services
    
    def clear(self) -> None:
        """Clear all services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._configurations.clear()
        self.logger.info("Cleared all services")


class ServiceProvider(ABC):
    """
    Abstract base class untuk service providers.
    """
    
    @abstractmethod
    def register(self, container: DependencyContainer) -> None:
        """
        Register services to container.
        
        Args:
            container: Dependency container
        """
        pass


class ConfigurationProvider(ServiceProvider):
    """
    Provider untuk configuration services.
    """
    
    def register(self, container: DependencyContainer) -> None:
        """Register configuration services."""
        # Register default configurations
        container.register_configuration('database', {
            'host': 'localhost',
            'port': 5432,
            'name': 'app_db'
        })
        
        container.register_configuration('cache', {
            'host': 'localhost',
            'port': 6379,
            'ttl': 3600
        })
        
        container.register_configuration('auth', {
            'secret_key': 'your-secret-key',
            'algorithm': 'HS256',
            'expire_minutes': 30
        })


class LoggingProvider(ServiceProvider):
    """
    Provider untuk logging services.
    """
    
    def register(self, container: DependencyContainer) -> None:
        """Register logging services."""
        def create_logger():
            logger = logging.getLogger('middleware')
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
            return logger
        
        container.register_singleton('logger', create_logger)


# Global dependency container
dependency_container = DependencyContainer()

# Register default providers
config_provider = ConfigurationProvider()
config_provider.register(dependency_container)

logging_provider = LoggingProvider()
logging_provider.register(dependency_container)

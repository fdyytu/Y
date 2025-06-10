"""
Base validator abstract class untuk semua validator middleware.
Mengikuti prinsip SOLID dan DRY.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Union
from fastapi import Request
import logging


class ValidationResult:
    """
    Result dari validasi.
    """
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None):
        """
        Initialize validation result.
        
        Args:
            is_valid: Apakah validasi berhasil
            errors: List error messages jika ada
            data: Data hasil validasi
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.data = data or {}
    
    def add_error(self, error: str) -> None:
        """
        Add error message.
        
        Args:
            error: Error message
        """
        self.errors.append(error)
        self.is_valid = False
    
    def has_errors(self) -> bool:
        """
        Check apakah ada errors.
        
        Returns:
            True jika ada errors
        """
        return len(self.errors) > 0


class BaseValidator(ABC):
    """
    Abstract base class untuk semua validator.
    Mengimplementasikan strategy pattern untuk validasi.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator dengan konfigurasi.
        
        Args:
            config: Dictionary konfigurasi validator
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup()
    
    def setup(self) -> None:
        """
        Setup validator. Override jika diperlukan.
        """
        pass
    
    @abstractmethod
    async def validate(self, data: Any, request: Optional[Request] = None) -> ValidationResult:
        """
        Validate data. Implementasi utama validator.
        
        Args:
            data: Data yang akan divalidasi
            request: FastAPI Request object (optional)
            
        Returns:
            ValidationResult object
        """
        pass
    
    async def validate_field(self, field_name: str, value: Any, rules: List[str]) -> ValidationResult:
        """
        Validate single field dengan rules.
        
        Args:
            field_name: Nama field
            value: Value yang akan divalidasi
            rules: List validation rules
            
        Returns:
            ValidationResult object
        """
        result = ValidationResult(True)
        
        for rule in rules:
            field_result = await self._apply_rule(field_name, value, rule)
            if not field_result.is_valid:
                result.errors.extend(field_result.errors)
                result.is_valid = False
        
        return result
    
    async def _apply_rule(self, field_name: str, value: Any, rule: str) -> ValidationResult:
        """
        Apply single validation rule.
        
        Args:
            field_name: Nama field
            value: Value yang akan divalidasi
            rule: Validation rule
            
        Returns:
            ValidationResult object
        """
        result = ValidationResult(True)
        
        if rule == 'required' and (value is None or value == ''):
            result.add_error(f"{field_name} is required")
        elif rule.startswith('min_length:'):
            min_len = int(rule.split(':')[1])
            if isinstance(value, str) and len(value) < min_len:
                result.add_error(f"{field_name} must be at least {min_len} characters")
        elif rule.startswith('max_length:'):
            max_len = int(rule.split(':')[1])
            if isinstance(value, str) and len(value) > max_len:
                result.add_error(f"{field_name} must not exceed {max_len} characters")
        elif rule == 'email' and value:
            if not self._is_valid_email(str(value)):
                result.add_error(f"{field_name} must be a valid email")
        
        return result
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Check apakah email valid.
        
        Args:
            email: Email string
            
        Returns:
            True jika email valid
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def is_enabled(self) -> bool:
        """
        Check apakah validator enabled.
        
        Returns:
            True jika validator enabled
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

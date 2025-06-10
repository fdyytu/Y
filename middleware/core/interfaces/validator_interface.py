"""
Interface untuk validator components.
Mengikuti prinsip Interface Segregation Principle (ISP).
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Union, Protocol
from fastapi import Request


class ValidationResult:
    """Result dari validasi."""
    
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.data = data or {}


class ValidatorInterface(Protocol):
    """
    Interface untuk validator components.
    """
    
    async def validate(self, data: Any, request: Optional[Request] = None) -> ValidationResult:
        """Validate data."""
        ...
    
    def get_rules(self) -> Dict[str, List[str]]:
        """Get validation rules."""
        ...


class InputValidatorInterface(Protocol):
    """
    Interface untuk input validator.
    """
    
    async def validate_input(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate input data."""
        ...
    
    async def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data."""
        ...


class SchemaValidatorInterface(Protocol):
    """
    Interface untuk schema validator.
    """
    
    async def validate_schema(self, data: Any, schema: Dict[str, Any]) -> ValidationResult:
        """Validate data against schema."""
        ...
    
    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """Load validation schema."""
        ...


class AuthValidatorInterface(Protocol):
    """
    Interface untuk authentication validator.
    """
    
    async def validate_credentials(self, credentials: Dict[str, Any]) -> ValidationResult:
        """Validate user credentials."""
        ...
    
    async def validate_token(self, token: str) -> ValidationResult:
        """Validate authentication token."""
        ...
    
    async def validate_permissions(self, user: Dict[str, Any], resource: str, action: str) -> ValidationResult:
        """Validate user permissions."""
        ...


class SecurityValidatorInterface(Protocol):
    """
    Interface untuk security validator.
    """
    
    async def validate_request_security(self, request: Request) -> ValidationResult:
        """Validate request security."""
        ...
    
    async def detect_malicious_input(self, data: Any) -> ValidationResult:
        """Detect malicious input."""
        ...
    
    async def validate_rate_limit(self, identifier: str) -> ValidationResult:
        """Validate rate limiting."""
        ...


class BusinessValidatorInterface(Protocol):
    """
    Interface untuk business logic validator.
    """
    
    async def validate_business_rules(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Validate business rules."""
        ...
    
    async def validate_constraints(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data constraints."""
        ...


class DataValidatorInterface(Protocol):
    """
    Interface untuk data validator.
    """
    
    async def validate_data_types(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data types."""
        ...
    
    async def validate_data_format(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data format."""
        ...
    
    async def validate_data_integrity(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data integrity."""
        ...


class FileValidatorInterface(Protocol):
    """
    Interface untuk file validator.
    """
    
    async def validate_file_type(self, file_data: bytes, allowed_types: List[str]) -> ValidationResult:
        """Validate file type."""
        ...
    
    async def validate_file_size(self, file_data: bytes, max_size: int) -> ValidationResult:
        """Validate file size."""
        ...
    
    async def scan_file_security(self, file_data: bytes) -> ValidationResult:
        """Scan file for security threats."""
        ...


class APIValidatorInterface(Protocol):
    """
    Interface untuk API validator.
    """
    
    async def validate_api_key(self, api_key: str) -> ValidationResult:
        """Validate API key."""
        ...
    
    async def validate_request_format(self, request: Request) -> ValidationResult:
        """Validate request format."""
        ...
    
    async def validate_response_format(self, response_data: Any) -> ValidationResult:
        """Validate response format."""
        ...

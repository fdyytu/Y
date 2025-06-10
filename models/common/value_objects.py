from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts."""
    amount: Decimal
    currency: str = "IDR"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")

@dataclass(frozen=True)
class Email:
    """Value object for email addresses."""
    value: str
    
    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError("Invalid email format")
            
    def _is_valid_email(self, email: str) -> bool:
        """Validasi format email sederhana."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

@dataclass(frozen=True)
class PhoneNumber:
    """Value object for phone numbers."""
    value: str
    country_code: str = "62"  # Indonesia
    
    def __post_init__(self):
        if not self._is_valid_phone(self.value):
            raise ValueError("Invalid phone number format")
            
    def _is_valid_phone(self, number: str) -> bool:
        """Validasi format nomor telepon Indonesia."""
        import re
        # Format: 08xxxxxxxxxx atau 8xxxxxxxxxx
        pattern = r'^0?8[0-9]{8,11}$'
        return re.match(pattern, number) is not None
    
    @property
    def formatted(self) -> str:
        """Format nomor dengan country code."""
        clean_number = self.value.lstrip('0')
        return f"+{self.country_code}{clean_number}"

@dataclass(frozen=True)
class Address:
    """Value object untuk alamat."""
    street: str
    city: str
    province: str
    postal_code: str
    country: str = "Indonesia"
    
    def __post_init__(self):
        if not all([self.street, self.city, self.province, self.postal_code]):
            raise ValueError("Semua field alamat harus diisi")
    
    @property
    def full_address(self) -> str:
        """Alamat lengkap dalam satu string."""
        return f"{self.street}, {self.city}, {self.province} {self.postal_code}, {self.country}"

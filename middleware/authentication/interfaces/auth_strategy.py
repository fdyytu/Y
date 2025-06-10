"""
Authentication strategy interface.
Mengikuti prinsip Interface Segregation Principle (ISP).
"""
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from datetime import datetime
from uuid import UUID


class TokenData:
    """Data class untuk token information."""
    
    def __init__(self, access_token: str, token_type: str = "bearer", expires_in: Optional[int] = None):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in


class AuthenticatedUser:
    """Data class untuk authenticated user."""
    
    def __init__(self, id: UUID, username: str, email: str, roles: Optional[list] = None):
        self.id = id
        self.username = username
        self.email = email
        self.roles = roles or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'roles': self.roles
        }


class AuthStrategy(ABC):
    """
    Abstract base class untuk authentication strategies.
    Mengimplementasikan Strategy Pattern.
    """
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[AuthenticatedUser]:
        """
        Authenticate user dengan credentials.
        
        Args:
            credentials: User credentials (username/password, api_key, etc.)
            
        Returns:
            AuthenticatedUser object atau None jika gagal
        """
        pass
        
    @abstractmethod
    async def create_token(self, user_id: UUID) -> TokenData:
        """
        Create authentication token untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            TokenData object
        """
        pass
        
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate authentication token.
        
        Args:
            token: Authentication token
            
        Returns:
            User data dictionary atau None jika token invalid
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Refresh authentication token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New TokenData atau None jika refresh gagal
        """
        pass
    
    def is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """
        Check apakah token sudah expired.
        
        Args:
            token_data: Token data dictionary
            
        Returns:
            True jika token expired
        """
        if 'exp' not in token_data:
            return False
        
        exp_timestamp = token_data['exp']
        current_timestamp = datetime.utcnow().timestamp()
        
        return current_timestamp > exp_timestamp

"""
Token service implementation.
Service untuk token generation, validation, dan management.
"""
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
import jwt
import secrets
import hashlib
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class TokenService:
    """
    Token Service untuk JWT dan token management.
    Menghandle token generation, validation, blacklisting, dan cleanup.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize token service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # JWT settings
        self.secret_key = config.get('secret_key', self._generate_secret_key())
        self.algorithm = config.get('algorithm', 'HS256')
        self.access_token_expire = config.get('access_token_expire', 3600)  # 1 hour
        self.refresh_token_expire = config.get('refresh_token_expire', 86400 * 7)  # 7 days
        
        # Token blacklist (in production, use Redis atau database)
        self.blacklisted_tokens: Set[str] = set()
        self.blacklisted_users: Set[str] = set()
        
        # Token storage untuk tracking
        self.active_tokens: Dict[str, Dict[str, Any]] = {}
        
    def _generate_secret_key(self) -> str:
        """Generate random secret key."""
        return secrets.token_urlsafe(32)
    
    def create_access_token(self, user_id: UUID, user_data: Dict[str, Any] = None, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User ID
            user_data: Additional user data untuk payload
            expires_delta: Custom expiration time
            
        Returns:
            JWT access token
        """
        try:
            # Calculate expiration
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(seconds=self.access_token_expire)
            
            # Create payload
            payload = {
                'sub': str(user_id),
                'type': 'access',
                'iat': datetime.utcnow(),
                'exp': expire,
                'jti': secrets.token_urlsafe(16)  # JWT ID untuk blacklisting
            }
            
            # Add user data
            if user_data:
                payload.update(user_data)
            
            # Generate token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            # Store token info
            self.active_tokens[token] = {
                'user_id': str(user_id),
                'type': 'access',
                'created_at': datetime.utcnow(),
                'expires_at': expire,
                'jti': payload['jti']
            }
            
            logger.debug(f"Created access token for user: {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    def create_refresh_token(self, user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create refresh token.
        
        Args:
            user_id: User ID
            expires_delta: Custom expiration time
            
        Returns:
            Refresh token
        """
        try:
            # Calculate expiration
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(seconds=self.refresh_token_expire)
            
            # Create payload
            payload = {
                'sub': str(user_id),
                'type': 'refresh',
                'iat': datetime.utcnow(),
                'exp': expire,
                'jti': secrets.token_urlsafe(16)
            }
            
            # Generate token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            # Store token info
            self.active_tokens[token] = {
                'user_id': str(user_id),
                'type': 'refresh',
                'created_at': datetime.utcnow(),
                'expires_at': expire,
                'jti': payload['jti']
            }
            
            logger.debug(f"Created refresh token for user: {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise
    
    def validate_token(self, token: str, token_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token.
        
        Args:
            token: JWT token
            token_type: Expected token type ('access' atau 'refresh')
            
        Returns:
            Token payload jika valid, None jika invalid
        """
        try:
            # Check blacklist
            if self._is_token_blacklisted(token):
                logger.warning("Token is blacklisted")
                return None
            
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if token_type and payload.get('type') != token_type:
                logger.warning(f"Token type mismatch. Expected: {token_type}, Got: {payload.get('type')}")
                return None
            
            # Check user blacklist
            user_id = payload.get('sub')
            if user_id and self._is_user_blacklisted(user_id):
                logger.warning(f"User {user_id} is blacklisted")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Create new access token dari refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary dengan new access token dan refresh token
        """
        try:
            # Validate refresh token
            payload = self.validate_token(refresh_token, token_type='refresh')
            if not payload:
                return None
            
            user_id = UUID(payload['sub'])
            
            # Create new access token
            new_access_token = self.create_access_token(user_id)
            
            # Optionally rotate refresh token
            if self.config.get('rotate_refresh_tokens', False):
                # Blacklist old refresh token
                self.blacklist_token(refresh_token)
                # Create new refresh token
                new_refresh_token = self.create_refresh_token(user_id)
            else:
                new_refresh_token = refresh_token
            
            return {
                'access_token': new_access_token,
                'refresh_token': new_refresh_token,
                'token_type': 'bearer'
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """
        Add token ke blacklist.
        
        Args:
            token: Token to blacklist
            
        Returns:
            True jika berhasil
        """
        try:
            # Get token hash untuk efficient storage
            token_hash = self._get_token_hash(token)
            self.blacklisted_tokens.add(token_hash)
            
            # Remove dari active tokens
            if token in self.active_tokens:
                del self.active_tokens[token]
            
            logger.debug("Token blacklisted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    def blacklist_user_tokens(self, user_id: UUID) -> bool:
        """
        Blacklist semua tokens untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            True jika berhasil
        """
        try:
            user_id_str = str(user_id)
            self.blacklisted_users.add(user_id_str)
            
            # Remove user tokens dari active tokens
            tokens_to_remove = []
            for token, info in self.active_tokens.items():
                if info['user_id'] == user_id_str:
                    tokens_to_remove.append(token)
            
            for token in tokens_to_remove:
                del self.active_tokens[token]
            
            logger.info(f"Blacklisted all tokens for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error blacklisting user tokens: {e}")
            return False
    
    def _is_token_blacklisted(self, token: str) -> bool:
        """Check apakah token ada di blacklist."""
        token_hash = self._get_token_hash(token)
        return token_hash in self.blacklisted_tokens
    
    def _is_user_blacklisted(self, user_id: str) -> bool:
        """Check apakah user ada di blacklist."""
        return user_id in self.blacklisted_users
    
    def _get_token_hash(self, token: str) -> str:
        """Get hash dari token untuk efficient storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get information tentang token.
        
        Args:
            token: JWT token
            
        Returns:
            Token information
        """
        try:
            payload = self.validate_token(token)
            if not payload:
                return None
            
            token_info = {
                'user_id': payload.get('sub'),
                'type': payload.get('type'),
                'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                'expires_at': datetime.fromtimestamp(payload.get('exp', 0)),
                'jti': payload.get('jti'),
                'is_expired': datetime.utcnow() > datetime.fromtimestamp(payload.get('exp', 0)),
                'is_blacklisted': self._is_token_blacklisted(token)
            }
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return None
    
    def get_user_tokens(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get semua active tokens untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of token information
        """
        user_id_str = str(user_id)
        user_tokens = []
        
        for token, info in self.active_tokens.items():
            if info['user_id'] == user_id_str:
                token_info = info.copy()
                token_info['token_hash'] = self._get_token_hash(token)
                user_tokens.append(token_info)
        
        return user_tokens
    
    async def cleanup_expired_tokens(self) -> int:
        """
        Cleanup expired tokens dari storage.
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            now = datetime.utcnow()
            expired_tokens = []
            
            # Find expired tokens
            for token, info in self.active_tokens.items():
                if info['expires_at'] < now:
                    expired_tokens.append(token)
            
            # Remove expired tokens
            for token in expired_tokens:
                del self.active_tokens[token]
            
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
            return len(expired_tokens)
            
        except Exception as e:
            logger.error(f"Token cleanup error: {e}")
            return 0
    
    def get_token_stats(self) -> Dict[str, Any]:
        """Get token statistics."""
        try:
            now = datetime.utcnow()
            active_count = 0
            expired_count = 0
            access_count = 0
            refresh_count = 0
            
            for info in self.active_tokens.values():
                if info['expires_at'] > now:
                    active_count += 1
                else:
                    expired_count += 1
                
                if info['type'] == 'access':
                    access_count += 1
                elif info['type'] == 'refresh':
                    refresh_count += 1
            
            return {
                'total_tokens': len(self.active_tokens),
                'active_tokens': active_count,
                'expired_tokens': expired_count,
                'access_tokens': access_count,
                'refresh_tokens': refresh_count,
                'blacklisted_tokens': len(self.blacklisted_tokens),
                'blacklisted_users': len(self.blacklisted_users)
            }
            
        except Exception as e:
            logger.error(f"Error getting token stats: {e}")
            return {}
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke token (alias untuk blacklist_token).
        
        Args:
            token: Token to revoke
            
        Returns:
            True jika berhasil
        """
        return self.blacklist_token(token)
    
    def is_token_valid(self, token: str) -> bool:
        """
        Quick check apakah token valid.
        
        Args:
            token: JWT token
            
        Returns:
            True jika valid
        """
        return self.validate_token(token) is not None

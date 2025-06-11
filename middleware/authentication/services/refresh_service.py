"""
Refresh service implementation.
Service untuk refresh token management dan rotation.
"""
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
import secrets
import hashlib
import logging
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class RefreshService:
    """
    Refresh Service untuk refresh token management.
    Menghandle refresh token generation, validation, rotation, dan cleanup.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize refresh service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Refresh token settings
        self.token_length = config.get('token_length', 32)
        self.default_expire_time = config.get('default_expire_time', 86400 * 7)  # 7 days
        self.max_tokens_per_user = config.get('max_tokens_per_user', 5)
        self.enable_rotation = config.get('enable_rotation', True)
        self.cleanup_interval = config.get('cleanup_interval', 3600)  # 1 hour
        
        # Token storage (in production, use Redis atau database)
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self.user_tokens: Dict[str, List[str]] = {}  # user_id -> [token_ids]
        self.revoked_tokens: Set[str] = set()
        
        # Token families untuk rotation tracking
        self.token_families: Dict[str, List[str]] = {}  # family_id -> [token_ids]
        
        # Last cleanup time
        self.last_cleanup = datetime.utcnow()
    
    def generate_refresh_token(self, user_id: UUID, expires_in: Optional[int] = None, device_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate new refresh token.
        
        Args:
            user_id: User ID
            expires_in: Token expiration dalam seconds
            device_info: Device information
            
        Returns:
            Refresh token
        """
        try:
            user_id_str = str(user_id)
            token_id = secrets.token_urlsafe(self.token_length)
            family_id = str(uuid4())
            
            # Calculate expiration
            expire_time = expires_in or self.default_expire_time
            expires_at = datetime.utcnow() + timedelta(seconds=expire_time)
            
            # Cleanup old tokens untuk user jika melebihi limit
            self._cleanup_user_tokens(user_id_str)
            
            # Create token data
            token_data = {
                'token_id': token_id,
                'user_id': user_id_str,
                'family_id': family_id,
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'device_info': device_info or {},
                'is_active': True,
                'usage_count': 0,
                'last_used': None
            }
            
            # Store token
            self.refresh_tokens[token_id] = token_data
            
            # Track user tokens
            if user_id_str not in self.user_tokens:
                self.user_tokens[user_id_str] = []
            self.user_tokens[user_id_str].append(token_id)
            
            # Track token family
            self.token_families[family_id] = [token_id]
            
            logger.debug(f"Generated refresh token for user {user_id}")
            return token_id
            
        except Exception as e:
            logger.error(f"Error generating refresh token: {e}")
            raise
    
    def validate_refresh_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate refresh token.
        
        Args:
            token_id: Refresh token ID
            
        Returns:
            Token data jika valid, None jika invalid
        """
        try:
            # Check if token exists
            token_data = self.refresh_tokens.get(token_id)
            if not token_data:
                logger.warning(f"Refresh token not found: {token_id}")
                return None
            
            # Check if token is revoked
            if token_id in self.revoked_tokens:
                logger.warning(f"Refresh token is revoked: {token_id}")
                return None
            
            # Check if token is active
            if not token_data.get('is_active', False):
                logger.warning(f"Refresh token is inactive: {token_id}")
                return None
            
            # Check expiration
            if datetime.utcnow() > token_data['expires_at']:
                logger.warning(f"Refresh token expired: {token_id}")
                self.revoke_token(token_id)
                return None
            
            # Update usage
            token_data['usage_count'] += 1
            token_data['last_used'] = datetime.utcnow()
            
            return token_data
            
        except Exception as e:
            logger.error(f"Refresh token validation error: {e}")
            return None
    
    def rotate_refresh_token(self, old_token_id: str, device_info: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Rotate refresh token (create new, revoke old).
        
        Args:
            old_token_id: Current refresh token
            device_info: Device information
            
        Returns:
            New refresh token atau None jika gagal
        """
        try:
            # Validate old token
            old_token_data = self.validate_refresh_token(old_token_id)
            if not old_token_data:
                return None
            
            user_id = UUID(old_token_data['user_id'])
            family_id = old_token_data['family_id']
            
            # Generate new token
            new_token_id = secrets.token_urlsafe(self.token_length)
            
            # Calculate expiration (same as old token remaining time atau default)
            remaining_time = (old_token_data['expires_at'] - datetime.utcnow()).total_seconds()
            expire_time = max(remaining_time, self.default_expire_time)
            expires_at = datetime.utcnow() + timedelta(seconds=expire_time)
            
            # Create new token data
            new_token_data = {
                'token_id': new_token_id,
                'user_id': old_token_data['user_id'],
                'family_id': family_id,
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'device_info': device_info or old_token_data.get('device_info', {}),
                'is_active': True,
                'usage_count': 0,
                'last_used': None,
                'parent_token': old_token_id
            }
            
            # Store new token
            self.refresh_tokens[new_token_id] = new_token_data
            
            # Update user tokens
            user_id_str = old_token_data['user_id']
            if user_id_str in self.user_tokens:
                if old_token_id in self.user_tokens[user_id_str]:
                    self.user_tokens[user_id_str].remove(old_token_id)
                self.user_tokens[user_id_str].append(new_token_id)
            
            # Update token family
            if family_id in self.token_families:
                self.token_families[family_id].append(new_token_id)
            
            # Revoke old token
            self.revoke_token(old_token_id)
            
            logger.debug(f"Rotated refresh token for user {user_id}")
            return new_token_id
            
        except Exception as e:
            logger.error(f"Token rotation error: {e}")
            return None
    
    def revoke_token(self, token_id: str) -> bool:
        """
        Revoke refresh token.
        
        Args:
            token_id: Token ID to revoke
            
        Returns:
            True jika berhasil
        """
        try:
            # Add to revoked set
            self.revoked_tokens.add(token_id)
            
            # Mark as inactive
            if token_id in self.refresh_tokens:
                self.refresh_tokens[token_id]['is_active'] = False
            
            logger.debug(f"Revoked refresh token: {token_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def revoke_token_family(self, token_id: str) -> int:
        """
        Revoke semua tokens dalam family (untuk security breach).
        
        Args:
            token_id: Any token dalam family
            
        Returns:
            Number of tokens revoked
        """
        try:
            token_data = self.refresh_tokens.get(token_id)
            if not token_data:
                return 0
            
            family_id = token_data['family_id']
            family_tokens = self.token_families.get(family_id, [])
            
            count = 0
            for family_token_id in family_tokens:
                if self.revoke_token(family_token_id):
                    count += 1
            
            logger.warning(f"Revoked {count} tokens in family {family_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error revoking token family: {e}")
            return 0
    
    def revoke_user_tokens(self, user_id: UUID) -> int:
        """
        Revoke semua refresh tokens untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of tokens revoked
        """
        try:
            user_id_str = str(user_id)
            token_ids = self.user_tokens.get(user_id_str, []).copy()
            
            count = 0
            for token_id in token_ids:
                if self.revoke_token(token_id):
                    count += 1
            
            # Clear user tokens list
            if user_id_str in self.user_tokens:
                del self.user_tokens[user_id_str]
            
            logger.info(f"Revoked {count} refresh tokens for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return 0
    
    def get_user_tokens(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get semua active refresh tokens untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of token information
        """
        try:
            user_id_str = str(user_id)
            token_ids = self.user_tokens.get(user_id_str, [])
            
            user_tokens = []
            for token_id in token_ids:
                token_data = self.refresh_tokens.get(token_id)
                if token_data and token_data.get('is_active', False) and token_id not in self.revoked_tokens:
                    # Remove sensitive data
                    safe_token = {
                        'token_id': token_data['token_id'],
                        'family_id': token_data['family_id'],
                        'created_at': token_data['created_at'],
                        'expires_at': token_data['expires_at'],
                        'device_info': token_data.get('device_info', {}),
                        'usage_count': token_data['usage_count'],
                        'last_used': token_data['last_used']
                    }
                    user_tokens.append(safe_token)
            
            return user_tokens
            
        except Exception as e:
            logger.error(f"Error getting user tokens: {e}")
            return []
    
    def cleanup_expired_tokens(self) -> int:
        """
        Cleanup expired dan revoked tokens.
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            now = datetime.utcnow()
            tokens_to_remove = []
            
            # Find expired atau revoked tokens
            for token_id, token_data in self.refresh_tokens.items():
                if (now > token_data['expires_at'] or 
                    token_id in self.revoked_tokens or 
                    not token_data.get('is_active', False)):
                    tokens_to_remove.append(token_id)
            
            # Remove tokens
            count = 0
            for token_id in tokens_to_remove:
                if self._remove_token(token_id):
                    count += 1
            
            # Cleanup revoked tokens set
            self.revoked_tokens = {
                token_id for token_id in self.revoked_tokens 
                if token_id in self.refresh_tokens
            }
            
            self.last_cleanup = now
            logger.info(f"Cleaned up {count} expired refresh tokens")
            return count
            
        except Exception as e:
            logger.error(f"Refresh token cleanup error: {e}")
            return 0
    
    def _cleanup_user_tokens(self, user_id: str) -> None:
        """Cleanup old tokens jika user melebihi limit."""
        try:
            token_ids = self.user_tokens.get(user_id, [])
            
            if len(token_ids) >= self.max_tokens_per_user:
                # Get token data dengan timestamps
                tokens_with_time = []
                for token_id in token_ids:
                    token_data = self.refresh_tokens.get(token_id)
                    if token_data and token_data.get('is_active', False):
                        tokens_with_time.append((token_id, token_data['created_at']))
                
                # Sort by created time (oldest first)
                tokens_with_time.sort(key=lambda x: x[1])
                
                # Remove oldest tokens
                tokens_to_remove = len(tokens_with_time) - self.max_tokens_per_user + 1
                for i in range(tokens_to_remove):
                    token_id = tokens_with_time[i][0]
                    self.revoke_token(token_id)
                    logger.debug(f"Removed old refresh token {token_id} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up user tokens: {e}")
    
    def _remove_token(self, token_id: str) -> bool:
        """Remove token dari semua storage."""
        try:
            # Remove dari refresh_tokens
            token_data = self.refresh_tokens.pop(token_id, None)
            if not token_data:
                return False
            
            # Remove dari user_tokens
            user_id = token_data['user_id']
            if user_id in self.user_tokens:
                if token_id in self.user_tokens[user_id]:
                    self.user_tokens[user_id].remove(token_id)
                
                # Clean up empty user token list
                if not self.user_tokens[user_id]:
                    del self.user_tokens[user_id]
            
            # Remove dari token_families
            family_id = token_data['family_id']
            if family_id in self.token_families:
                if token_id in self.token_families[family_id]:
                    self.token_families[family_id].remove(token_id)
                
                # Clean up empty family
                if not self.token_families[family_id]:
                    del self.token_families[family_id]
            
            # Remove dari revoked_tokens
            self.revoked_tokens.discard(token_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing token: {e}")
            return False
    
    def get_token_stats(self) -> Dict[str, Any]:
        """Get refresh token statistics."""
        try:
            now = datetime.utcnow()
            active_count = 0
            expired_count = 0
            revoked_count = len(self.revoked_tokens)
            
            for token_data in self.refresh_tokens.values():
                if now > token_data['expires_at']:
                    expired_count += 1
                elif token_data.get('is_active', False):
                    active_count += 1
            
            return {
                'total_tokens': len(self.refresh_tokens),
                'active_tokens': active_count,
                'expired_tokens': expired_count,
                'revoked_tokens': revoked_count,
                'total_users': len(self.user_tokens),
                'total_families': len(self.token_families),
                'max_tokens_per_user': self.max_tokens_per_user,
                'rotation_enabled': self.enable_rotation,
                'last_cleanup': self.last_cleanup
            }
            
        except Exception as e:
            logger.error(f"Error getting token stats: {e}")
            return {}
    
    def should_cleanup(self) -> bool:
        """Check apakah perlu cleanup."""
        time_since_cleanup = datetime.utcnow() - self.last_cleanup
        return time_since_cleanup.total_seconds() >= self.cleanup_interval

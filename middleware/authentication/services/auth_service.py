"""
Authentication service implementation.
Core service untuk authentication operations.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from uuid import UUID, uuid4

from ..interfaces.auth_strategy import AuthStrategy, AuthenticatedUser, TokenData
from .token_service import TokenService
from .session_service import SessionService
from .user_service import UserService

logger = logging.getLogger(__name__)


class AuthService:
    """
    Core Authentication Service.
    Menghandle authentication operations dan koordinasi antar services.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize authentication service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.strategies: Dict[str, AuthStrategy] = {}
        self.default_strategy: Optional[str] = None
        
        # Initialize dependent services
        self.token_service = TokenService(config.get('token', {}))
        self.session_service = SessionService(config.get('session', {}))
        self.user_service = UserService(config.get('user', {}))
        
        # Authentication settings
        self.max_login_attempts = config.get('max_login_attempts', 5)
        self.lockout_duration = config.get('lockout_duration', 300)  # 5 minutes
        self.session_timeout = config.get('session_timeout', 3600)  # 1 hour
        
        # Track login attempts
        self.login_attempts: Dict[str, List[datetime]] = {}
        
    def register_strategy(self, name: str, strategy: AuthStrategy, is_default: bool = False) -> None:
        """
        Register authentication strategy.
        
        Args:
            name: Strategy name
            strategy: AuthStrategy instance
            is_default: Set as default strategy
        """
        self.strategies[name] = strategy
        
        if is_default or not self.default_strategy:
            self.default_strategy = name
        
        logger.info(f"Registered auth strategy: {name}")
    
    def get_strategy(self, name: Optional[str] = None) -> Optional[AuthStrategy]:
        """
        Get authentication strategy.
        
        Args:
            name: Strategy name (uses default if None)
            
        Returns:
            AuthStrategy instance atau None
        """
        strategy_name = name or self.default_strategy
        return self.strategies.get(strategy_name)
    
    async def authenticate(self, credentials: Dict[str, Any], strategy_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Authenticate user dengan credentials.
        
        Args:
            credentials: User credentials
            strategy_name: Strategy to use (optional)
            
        Returns:
            Authentication result dengan user data dan tokens
        """
        try:
            # Get strategy
            strategy = self.get_strategy(strategy_name)
            if not strategy:
                logger.error(f"Strategy '{strategy_name}' not found")
                return None
            
            # Check rate limiting
            user_identifier = credentials.get('username') or credentials.get('email', 'unknown')
            if self._is_rate_limited(user_identifier):
                logger.warning(f"Rate limited login attempt for: {user_identifier}")
                return None
            
            # Authenticate with strategy
            user = await strategy.authenticate(credentials)
            if not user:
                self._record_failed_attempt(user_identifier)
                return None
            
            # Clear failed attempts on successful auth
            self._clear_failed_attempts(user_identifier)
            
            # Create tokens
            token_data = await strategy.create_token(user.id)
            
            # Create session
            session_id = await self.session_service.create_session(
                user_id=user.id,
                user_data=user.to_dict(),
                expires_in=self.session_timeout
            )
            
            # Prepare result
            result = {
                'user': user.to_dict(),
                'tokens': {
                    'access_token': token_data.access_token,
                    'token_type': token_data.token_type,
                    'expires_in': token_data.expires_in
                },
                'session_id': session_id,
                'authenticated_at': datetime.utcnow().isoformat(),
                'strategy': strategy_name or self.default_strategy
            }
            
            logger.info(f"User authenticated successfully: {user.username}")
            return result
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def validate_token(self, token: str, strategy_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Validate authentication token.
        
        Args:
            token: Authentication token
            strategy_name: Strategy to use for validation
            
        Returns:
            User data jika valid, None jika invalid
        """
        try:
            # Try all strategies if none specified
            strategies_to_try = []
            if strategy_name:
                strategy = self.get_strategy(strategy_name)
                if strategy:
                    strategies_to_try.append((strategy_name, strategy))
            else:
                strategies_to_try = list(self.strategies.items())
            
            for name, strategy in strategies_to_try:
                user_data = await strategy.validate_token(token)
                if user_data:
                    # Validate session if user has session_id
                    if 'session_id' in user_data:
                        session_valid = await self.session_service.validate_session(
                            user_data['session_id']
                        )
                        if not session_valid:
                            continue
                    
                    # Add strategy info
                    user_data['auth_strategy'] = name
                    return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str, strategy_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Refresh authentication token.
        
        Args:
            refresh_token: Refresh token
            strategy_name: Strategy to use
            
        Returns:
            New token data atau None jika gagal
        """
        try:
            strategy = self.get_strategy(strategy_name)
            if not strategy:
                return None
            
            new_token_data = await strategy.refresh_token(refresh_token)
            if not new_token_data:
                return None
            
            return {
                'access_token': new_token_data.access_token,
                'token_type': new_token_data.token_type,
                'expires_in': new_token_data.expires_in,
                'refreshed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    async def logout(self, token: str, session_id: Optional[str] = None) -> bool:
        """
        Logout user dan invalidate tokens/sessions.
        
        Args:
            token: Access token
            session_id: Session ID (optional)
            
        Returns:
            True jika berhasil
        """
        try:
            success = True
            
            # Invalidate session
            if session_id:
                await self.session_service.invalidate_session(session_id)
            
            # Add token to blacklist
            await self.token_service.blacklist_token(token)
            
            logger.info("User logged out successfully")
            return success
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    async def logout_all_sessions(self, user_id: UUID) -> bool:
        """
        Logout user dari semua sessions.
        
        Args:
            user_id: User ID
            
        Returns:
            True jika berhasil
        """
        try:
            # Invalidate all user sessions
            await self.session_service.invalidate_user_sessions(user_id)
            
            # Blacklist all user tokens (if supported)
            await self.token_service.blacklist_user_tokens(user_id)
            
            logger.info(f"All sessions logged out for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Logout all sessions error: {e}")
            return False
    
    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True jika berhasil
        """
        try:
            # Validate old password
            user = await self.user_service.get_user(user_id)
            if not user:
                return False
            
            # Verify old password
            if not await self.user_service.verify_password(user_id, old_password):
                return False
            
            # Update password
            success = await self.user_service.update_password(user_id, new_password)
            
            if success:
                # Logout all sessions untuk security
                await self.logout_all_sessions(user_id)
                logger.info(f"Password changed for user: {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Change password error: {e}")
            return False
    
    async def get_user_sessions(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get active sessions untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        try:
            return await self.session_service.get_user_sessions(user_id)
        except Exception as e:
            logger.error(f"Get user sessions error: {e}")
            return []
    
    def _is_rate_limited(self, identifier: str) -> bool:
        """Check apakah identifier sedang rate limited."""
        if identifier not in self.login_attempts:
            return False
        
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.lockout_duration)
        
        # Remove old attempts
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier]
            if attempt > cutoff
        ]
        
        # Check if exceeded max attempts
        return len(self.login_attempts[identifier]) >= self.max_login_attempts
    
    def _record_failed_attempt(self, identifier: str) -> None:
        """Record failed login attempt."""
        if identifier not in self.login_attempts:
            self.login_attempts[identifier] = []
        
        self.login_attempts[identifier].append(datetime.utcnow())
    
    def _clear_failed_attempts(self, identifier: str) -> None:
        """Clear failed login attempts."""
        if identifier in self.login_attempts:
            del self.login_attempts[identifier]
    
    async def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        try:
            stats = {
                'strategies': list(self.strategies.keys()),
                'default_strategy': self.default_strategy,
                'active_sessions': await self.session_service.get_active_session_count(),
                'rate_limited_users': len(self.login_attempts),
                'config': {
                    'max_login_attempts': self.max_login_attempts,
                    'lockout_duration': self.lockout_duration,
                    'session_timeout': self.session_timeout
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Get auth stats error: {e}")
            return {}
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Cleanup expired tokens, sessions, etc."""
        try:
            results = {
                'expired_sessions': 0,
                'expired_tokens': 0,
                'cleared_attempts': 0
            }
            
            # Cleanup expired sessions
            results['expired_sessions'] = await self.session_service.cleanup_expired_sessions()
            
            # Cleanup expired tokens
            results['expired_tokens'] = await self.token_service.cleanup_expired_tokens()
            
            # Clear old login attempts
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.lockout_duration * 2)
            
            for identifier in list(self.login_attempts.keys()):
                self.login_attempts[identifier] = [
                    attempt for attempt in self.login_attempts[identifier]
                    if attempt > cutoff
                ]
                if not self.login_attempts[identifier]:
                    del self.login_attempts[identifier]
                    results['cleared_attempts'] += 1
            
            logger.info(f"Cleanup completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return {}

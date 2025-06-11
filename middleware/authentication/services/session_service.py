"""
Session service implementation.
Service untuk session management dan tracking.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import secrets
import logging
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class SessionService:
    """
    Session Service untuk session management.
    Menghandle session creation, validation, cleanup, dan multi-device support.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize session service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Session settings
        self.default_session_timeout = config.get('session_timeout', 3600)  # 1 hour
        self.max_sessions_per_user = config.get('max_sessions_per_user', 5)
        self.cleanup_interval = config.get('cleanup_interval', 300)  # 5 minutes
        
        # Session storage (in production, use Redis atau database)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        
        # Last cleanup time
        self.last_cleanup = datetime.utcnow()
    
    async def create_session(self, user_id: UUID, user_data: Dict[str, Any], expires_in: Optional[int] = None, device_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new session untuk user.
        
        Args:
            user_id: User ID
            user_data: User data untuk session
            expires_in: Session timeout dalam seconds
            device_info: Device information
            
        Returns:
            Session ID
        """
        try:
            user_id_str = str(user_id)
            session_id = str(uuid4())
            
            # Calculate expiration
            timeout = expires_in or self.default_session_timeout
            expires_at = datetime.utcnow() + timedelta(seconds=timeout)
            
            # Cleanup old sessions untuk user jika melebihi limit
            await self._cleanup_user_sessions(user_id_str)
            
            # Create session data
            session_data = {
                'session_id': session_id,
                'user_id': user_id_str,
                'user_data': user_data,
                'created_at': datetime.utcnow(),
                'last_accessed': datetime.utcnow(),
                'expires_at': expires_at,
                'device_info': device_info or {},
                'is_active': True
            }
            
            # Store session
            self.sessions[session_id] = session_data
            
            # Track user sessions
            if user_id_str not in self.user_sessions:
                self.user_sessions[user_id_str] = []
            self.user_sessions[user_id_str].append(session_id)
            
            logger.debug(f"Created session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def validate_session(self, session_id: str, update_last_accessed: bool = True) -> bool:
        """
        Validate session dan check expiration.
        
        Args:
            session_id: Session ID
            update_last_accessed: Update last accessed time
            
        Returns:
            True jika session valid
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # Check if session is active
            if not session.get('is_active', False):
                return False
            
            # Check expiration
            if datetime.utcnow() > session['expires_at']:
                await self.invalidate_session(session_id)
                return False
            
            # Update last accessed
            if update_last_accessed:
                session['last_accessed'] = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data atau None jika tidak ada
        """
        try:
            if not await self.validate_session(session_id):
                return None
            
            return self.sessions.get(session_id)
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session ID
            data: Data untuk update
            
        Returns:
            True jika berhasil
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Update data
            session.update(data)
            session['last_accessed'] = datetime.utcnow()
            
            logger.debug(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    async def extend_session(self, session_id: str, additional_time: int) -> bool:
        """
        Extend session expiration time.
        
        Args:
            session_id: Session ID
            additional_time: Additional time dalam seconds
            
        Returns:
            True jika berhasil
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # Extend expiration
            session['expires_at'] += timedelta(seconds=additional_time)
            session['last_accessed'] = datetime.utcnow()
            
            logger.debug(f"Extended session {session_id} by {additional_time} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            return False
    
    async def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True jika berhasil
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            user_id = session['user_id']
            
            # Remove session
            del self.sessions[session_id]
            
            # Remove dari user sessions
            if user_id in self.user_sessions:
                if session_id in self.user_sessions[user_id]:
                    self.user_sessions[user_id].remove(session_id)
                
                # Clean up empty user session list
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
            
            logger.debug(f"Invalidated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    async def invalidate_user_sessions(self, user_id: UUID) -> int:
        """
        Invalidate semua sessions untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions invalidated
        """
        try:
            user_id_str = str(user_id)
            session_ids = self.user_sessions.get(user_id_str, []).copy()
            
            count = 0
            for session_id in session_ids:
                if await self.invalidate_session(session_id):
                    count += 1
            
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating user sessions: {e}")
            return 0
    
    async def get_user_sessions(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get semua active sessions untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of session data
        """
        try:
            user_id_str = str(user_id)
            session_ids = self.user_sessions.get(user_id_str, [])
            
            user_sessions = []
            for session_id in session_ids.copy():  # Copy to avoid modification during iteration
                session = await self.get_session(session_id)
                if session:
                    # Remove sensitive data
                    safe_session = {
                        'session_id': session['session_id'],
                        'created_at': session['created_at'],
                        'last_accessed': session['last_accessed'],
                        'expires_at': session['expires_at'],
                        'device_info': session.get('device_info', {}),
                        'is_active': session['is_active']
                    }
                    user_sessions.append(safe_session)
            
            return user_sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def get_active_session_count(self) -> int:
        """Get jumlah active sessions."""
        try:
            count = 0
            for session_id in list(self.sessions.keys()):
                if await self.validate_session(session_id, update_last_accessed=False):
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Error getting active session count: {e}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Cleanup expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            now = datetime.utcnow()
            expired_sessions = []
            
            # Find expired sessions
            for session_id, session in self.sessions.items():
                if now > session['expires_at']:
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            count = 0
            for session_id in expired_sessions:
                if await self.invalidate_session(session_id):
                    count += 1
            
            self.last_cleanup = now
            logger.info(f"Cleaned up {count} expired sessions")
            return count
            
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            return 0
    
    async def _cleanup_user_sessions(self, user_id: str) -> None:
        """Cleanup old sessions jika user melebihi limit."""
        try:
            session_ids = self.user_sessions.get(user_id, [])
            
            if len(session_ids) >= self.max_sessions_per_user:
                # Get session data dengan timestamps
                sessions_with_time = []
                for session_id in session_ids:
                    session = self.sessions.get(session_id)
                    if session:
                        sessions_with_time.append((session_id, session['last_accessed']))
                
                # Sort by last accessed (oldest first)
                sessions_with_time.sort(key=lambda x: x[1])
                
                # Remove oldest sessions
                sessions_to_remove = len(sessions_with_time) - self.max_sessions_per_user + 1
                for i in range(sessions_to_remove):
                    session_id = sessions_with_time[i][0]
                    await self.invalidate_session(session_id)
                    logger.debug(f"Removed old session {session_id} for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up user sessions: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        try:
            now = datetime.utcnow()
            active_count = 0
            expired_count = 0
            
            for session in self.sessions.values():
                if now > session['expires_at']:
                    expired_count += 1
                else:
                    active_count += 1
            
            return {
                'total_sessions': len(self.sessions),
                'active_sessions': active_count,
                'expired_sessions': expired_count,
                'total_users': len(self.user_sessions),
                'max_sessions_per_user': self.max_sessions_per_user,
                'last_cleanup': self.last_cleanup
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}
    
    async def should_cleanup(self) -> bool:
        """Check apakah perlu cleanup."""
        time_since_cleanup = datetime.utcnow() - self.last_cleanup
        return time_since_cleanup.total_seconds() >= self.cleanup_interval

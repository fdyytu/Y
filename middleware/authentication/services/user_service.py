"""
User service implementation.
Service untuk user management dalam context authentication.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import secrets
import logging
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class UserService:
    """
    User Service untuk user management.
    Menghandle user lookup, validation, role/permission management dalam context authentication.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize user service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # User storage (in production, use database)
        self.users: Dict[str, Dict[str, Any]] = {}
        self.user_by_email: Dict[str, str] = {}  # email -> user_id
        self.user_by_username: Dict[str, str] = {}  # username -> user_id
        
        # Password settings
        self.password_salt_length = config.get('password_salt_length', 32)
        self.password_iterations = config.get('password_iterations', 100000)
        
        # Role and permission settings
        self.default_roles = config.get('default_roles', ['user'])
        self.role_hierarchy = config.get('role_hierarchy', {
            'admin': ['moderator', 'user'],
            'moderator': ['user'],
            'user': []
        })
        
    async def get_user(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User data atau None jika tidak ditemukan
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if user_data:
                # Return copy tanpa sensitive data
                safe_user = user_data.copy()
                safe_user.pop('password_hash', None)
                safe_user.pop('password_salt', None)
                return safe_user
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User data atau None jika tidak ditemukan
        """
        try:
            user_id = self.user_by_email.get(email.lower())
            if user_id:
                return await self.get_user(UUID(user_id))
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username.
        
        Args:
            username: Username
            
        Returns:
            User data atau None jika tidak ditemukan
        """
        try:
            user_id = self.user_by_username.get(username.lower())
            if user_id:
                return await self.get_user(UUID(user_id))
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[UUID]:
        """
        Create new user.
        
        Args:
            user_data: User data (username, email, password, etc.)
            
        Returns:
            User ID jika berhasil, None jika gagal
        """
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if field not in user_data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            username = user_data['username'].lower()
            email = user_data['email'].lower()
            
            # Check if user already exists
            if username in self.user_by_username:
                logger.error(f"Username already exists: {username}")
                return None
            
            if email in self.user_by_email:
                logger.error(f"Email already exists: {email}")
                return None
            
            # Generate user ID
            user_id = uuid4()
            user_id_str = str(user_id)
            
            # Hash password
            password_salt = secrets.token_bytes(self.password_salt_length)
            password_hash = self._hash_password(user_data['password'], password_salt)
            
            # Create user record
            user_record = {
                'user_id': user_id_str,
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'password_salt': password_salt,
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
                'is_active': user_data.get('is_active', True),
                'is_verified': user_data.get('is_verified', False),
                'roles': user_data.get('roles', self.default_roles.copy()),
                'permissions': user_data.get('permissions', []),
                'metadata': user_data.get('metadata', {}),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'last_login': None
            }
            
            # Store user
            self.users[user_id_str] = user_record
            self.user_by_email[email] = user_id_str
            self.user_by_username[username] = user_id_str
            
            logger.info(f"Created user: {username} ({email})")
            return user_id
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def verify_password(self, user_id: UUID, password: str) -> bool:
        """
        Verify user password.
        
        Args:
            user_id: User ID
            password: Password to verify
            
        Returns:
            True jika password benar
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if not user_data:
                return False
            
            stored_hash = user_data['password_hash']
            salt = user_data['password_salt']
            
            # Hash provided password dengan salt yang sama
            password_hash = self._hash_password(password, salt)
            
            return password_hash == stored_hash
            
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """
        Update user password.
        
        Args:
            user_id: User ID
            new_password: New password
            
        Returns:
            True jika berhasil
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if not user_data:
                return False
            
            # Generate new salt dan hash
            password_salt = secrets.token_bytes(self.password_salt_length)
            password_hash = self._hash_password(new_password, password_salt)
            
            # Update password
            user_data['password_hash'] = password_hash
            user_data['password_salt'] = password_salt
            user_data['updated_at'] = datetime.utcnow()
            
            logger.info(f"Updated password for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating password: {e}")
            return False
    
    async def update_last_login(self, user_id: UUID) -> bool:
        """
        Update user last login time.
        
        Args:
            user_id: User ID
            
        Returns:
            True jika berhasil
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if not user_data:
                return False
            
            user_data['last_login'] = datetime.utcnow()
            return True
            
        except Exception as e:
            logger.error(f"Error updating last login: {e}")
            return False
    
    async def has_role(self, user_id: UUID, role: str) -> bool:
        """
        Check if user has specific role.
        
        Args:
            user_id: User ID
            role: Role to check
            
        Returns:
            True jika user memiliki role
        """
        try:
            user_data = await self.get_user(user_id)
            if not user_data:
                return False
            
            user_roles = user_data.get('roles', [])
            
            # Check direct role
            if role in user_roles:
                return True
            
            # Check role hierarchy
            for user_role in user_roles:
                if role in self.role_hierarchy.get(user_role, []):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking user role: {e}")
            return False
    
    async def has_permission(self, user_id: UUID, permission: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user_id: User ID
            permission: Permission to check
            
        Returns:
            True jika user memiliki permission
        """
        try:
            user_data = await self.get_user(user_id)
            if not user_data:
                return False
            
            user_permissions = user_data.get('permissions', [])
            return permission in user_permissions
            
        except Exception as e:
            logger.error(f"Error checking user permission: {e}")
            return False
    
    async def add_role(self, user_id: UUID, role: str) -> bool:
        """
        Add role to user.
        
        Args:
            user_id: User ID
            role: Role to add
            
        Returns:
            True jika berhasil
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if not user_data:
                return False
            
            if role not in user_data['roles']:
                user_data['roles'].append(role)
                user_data['updated_at'] = datetime.utcnow()
                logger.info(f"Added role '{role}' to user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding role: {e}")
            return False
    
    async def remove_role(self, user_id: UUID, role: str) -> bool:
        """
        Remove role from user.
        
        Args:
            user_id: User ID
            role: Role to remove
            
        Returns:
            True jika berhasil
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if not user_data:
                return False
            
            if role in user_data['roles']:
                user_data['roles'].remove(role)
                user_data['updated_at'] = datetime.utcnow()
                logger.info(f"Removed role '{role}' from user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing role: {e}")
            return False
    
    async def add_permission(self, user_id: UUID, permission: str) -> bool:
        """
        Add permission to user.
        
        Args:
            user_id: User ID
            permission: Permission to add
            
        Returns:
            True jika berhasil
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if not user_data:
                return False
            
            if permission not in user_data['permissions']:
                user_data['permissions'].append(permission)
                user_data['updated_at'] = datetime.utcnow()
                logger.info(f"Added permission '{permission}' to user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding permission: {e}")
            return False
    
    async def remove_permission(self, user_id: UUID, permission: str) -> bool:
        """
        Remove permission from user.
        
        Args:
            user_id: User ID
            permission: Permission to remove
            
        Returns:
            True jika berhasil
        """
        try:
            user_id_str = str(user_id)
            user_data = self.users.get(user_id_str)
            
            if not user_data:
                return False
            
            if permission in user_data['permissions']:
                user_data['permissions'].remove(permission)
                user_data['updated_at'] = datetime.utcnow()
                logger.info(f"Removed permission '{permission}' from user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing permission: {e}")
            return False
    
    def _hash_password(self, password: str, salt: bytes) -> bytes:
        """Hash password dengan salt."""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            self.password_iterations
        )
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            total_users = len(self.users)
            active_users = sum(1 for user in self.users.values() if user.get('is_active', False))
            verified_users = sum(1 for user in self.users.values() if user.get('is_verified', False))
            
            # Role distribution
            role_counts = {}
            for user in self.users.values():
                for role in user.get('roles', []):
                    role_counts[role] = role_counts.get(role, 0) + 1
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'verified_users': verified_users,
                'inactive_users': total_users - active_users,
                'unverified_users': total_users - verified_users,
                'role_distribution': role_counts,
                'default_roles': self.default_roles,
                'role_hierarchy': self.role_hierarchy
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}

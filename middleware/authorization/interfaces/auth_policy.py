"""
Authorization policy interface.
Mengikuti prinsip Interface Segregation Principle (ISP).
"""
from abc import ABC, abstractmethod
from typing import Set, List, Dict, Any, Optional
from uuid import UUID


class AuthorizationPolicy(ABC):
    """
    Abstract base class untuk authorization policies.
    Mengimplementasikan Strategy Pattern untuk authorization.
    """
    
    @abstractmethod
    async def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """
        Get all permissions untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            Set of permission strings
        """
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: UUID) -> Set[str]:
        """
        Get all roles untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            Set of role names
        """
        pass
    
    @abstractmethod
    async def assign_user_role(self, user_id: UUID, role_name: str) -> None:
        """
        Assign role ke user.
        
        Args:
            user_id: User ID
            role_name: Role name
        """
        pass
    
    @abstractmethod
    async def revoke_user_role(self, user_id: UUID, role_name: str) -> None:
        """
        Revoke role dari user.
        
        Args:
            user_id: User ID
            role_name: Role name
        """
        pass
    
    @abstractmethod
    async def check_permission(self, user_id: UUID, permission: str) -> bool:
        """
        Check apakah user memiliki permission tertentu.
        
        Args:
            user_id: User ID
            permission: Permission string
            
        Returns:
            True jika user memiliki permission
        """
        pass
    
    @abstractmethod
    async def get_role_permissions(self, role_name: str) -> Set[str]:
        """
        Get all permissions untuk role.
        
        Args:
            role_name: Role name
            
        Returns:
            Set of permission strings
        """
        pass
    
    @abstractmethod
    async def create_role(self, role_name: str, permissions: Set[str]) -> None:
        """
        Create new role dengan permissions.
        
        Args:
            role_name: Role name
            permissions: Set of permission strings
        """
        pass
    
    @abstractmethod
    async def delete_role(self, role_name: str) -> None:
        """
        Delete role.
        
        Args:
            role_name: Role name
        """
        pass
    
    @abstractmethod
    async def add_role_permission(self, role_name: str, permission: str) -> None:
        """
        Add permission ke role.
        
        Args:
            role_name: Role name
            permission: Permission string
        """
        pass
    
    @abstractmethod
    async def remove_role_permission(self, role_name: str, permission: str) -> None:
        """
        Remove permission dari role.
        
        Args:
            role_name: Role name
            permission: Permission string
        """
        pass


class RBACPolicy(AuthorizationPolicy):
    """
    Role-Based Access Control (RBAC) policy implementation.
    """
    
    def __init__(self):
        """Initialize RBAC policy."""
        # In-memory storage untuk demo
        # Dalam implementasi nyata, ini akan menggunakan database
        self.user_roles: Dict[UUID, Set[str]] = {}
        self.role_permissions: Dict[str, Set[str]] = {
            'admin': {'*'},  # Admin memiliki semua permissions
            'user': {'read'},
            'moderator': {'read', 'update'}
        }
    
    async def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """Get all permissions untuk user."""
        permissions = set()
        user_roles = await self.get_user_roles(user_id)
        
        for role in user_roles:
            role_perms = await self.get_role_permissions(role)
            permissions.update(role_perms)
        
        return permissions
    
    async def get_user_roles(self, user_id: UUID) -> Set[str]:
        """Get all roles untuk user."""
        return self.user_roles.get(user_id, set())
    
    async def assign_user_role(self, user_id: UUID, role_name: str) -> None:
        """Assign role ke user."""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role_name)
    
    async def revoke_user_role(self, user_id: UUID, role_name: str) -> None:
        """Revoke role dari user."""
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role_name)
    
    async def check_permission(self, user_id: UUID, permission: str) -> bool:
        """Check apakah user memiliki permission."""
        user_permissions = await self.get_user_permissions(user_id)
        
        # Check for wildcard permission (admin)
        if '*' in user_permissions:
            return True
        
        return permission in user_permissions
    
    async def get_role_permissions(self, role_name: str) -> Set[str]:
        """Get all permissions untuk role."""
        return self.role_permissions.get(role_name, set())
    
    async def create_role(self, role_name: str, permissions: Set[str]) -> None:
        """Create new role."""
        self.role_permissions[role_name] = permissions
    
    async def delete_role(self, role_name: str) -> None:
        """Delete role."""
        if role_name in self.role_permissions:
            del self.role_permissions[role_name]
        
        # Remove role dari semua users
        for user_id in self.user_roles:
            self.user_roles[user_id].discard(role_name)
    
    async def add_role_permission(self, role_name: str, permission: str) -> None:
        """Add permission ke role."""
        if role_name not in self.role_permissions:
            self.role_permissions[role_name] = set()
        self.role_permissions[role_name].add(permission)
    
    async def remove_role_permission(self, role_name: str, permission: str) -> None:
        """Remove permission dari role."""
        if role_name in self.role_permissions:
            self.role_permissions[role_name].discard(permission)

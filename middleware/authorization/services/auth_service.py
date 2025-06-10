"""
Authorization service menggunakan base handler.
Mengikuti prinsip SOLID dan DRY.
"""
from typing import List, Set, Dict, Any, Optional, Union
from uuid import UUID
from fastapi import Request, Response, HTTPException
from middleware.core.abstract.base_handler import BaseHandler
from middleware.core.interfaces.middleware_interface import AuthorizationInterface
from ..interfaces.auth_policy import AuthorizationPolicy


class AuthorizationService(BaseHandler, AuthorizationInterface):
    """
    Authorization service yang mengextend BaseHandler.
    Mengimplementasikan AuthorizationInterface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize authorization service.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.policy: Optional[AuthorizationPolicy] = None
    
    def setup(self) -> None:
        """Setup authorization policy dari config."""
        policy_name = self.get_config('policy_name', 'rbac')
        
        # Get policy from dependency container
        from middleware.core.registry.dependency_container import dependency_container
        self.policy = dependency_container.get_service(f"auth_policy_{policy_name}")
        
        if not self.policy:
            raise ValueError(f"Authorization policy '{policy_name}' not found in dependency container")
    
    async def handle(self, request: Request, **kwargs) -> Union[Request, Response, Any]:
        """
        Handle authorization request.
        
        Args:
            request: FastAPI Request object
            **kwargs: Additional arguments (resource, action, etc.)
            
        Returns:
            Modified request jika authorized
            
        Raises:
            HTTPException: Jika tidak authorized
        """
        # Get user dari request state
        user = getattr(request.state, 'user', None)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required for authorization"
            )
        
        # Get resource dan action dari kwargs
        resource = kwargs.get('resource', self._extract_resource(request))
        action = kwargs.get('action', self._extract_action(request))
        
        # Check authorization
        is_authorized = await self.authorize(request, resource, action)
        if not is_authorized:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied for {action} on {resource}"
            )
        
        self.log_info(f"User {user.get('id')} authorized for {action} on {resource}")
        return request
    
    async def authorize(self, request: Request, resource: str, action: str) -> bool:
        """
        Authorize request untuk resource dan action.
        
        Args:
            request: FastAPI Request object
            resource: Resource yang diakses
            action: Action yang dilakukan
            
        Returns:
            True jika authorized
        """
        try:
            user = getattr(request.state, 'user', None)
            if not user:
                return False
            
            user_id = UUID(user['id'])
            
            # Check permission menggunakan policy
            return await self.check_permission(user_id, resource, action)
            
        except Exception as e:
            self.log_error(f"Authorization error: {str(e)}", exc=e)
            return False
    
    async def check_permission(self, user_id: UUID, resource: str, action: str) -> bool:
        """
        Check permission untuk user, resource, dan action.
        
        Args:
            user_id: User ID
            resource: Resource yang diakses
            action: Action yang dilakukan
            
        Returns:
            True jika user memiliki permission
        """
        try:
            # Get required permissions untuk resource dan action
            required_permissions = self._get_required_permissions(resource, action)
            
            # Get user permissions dari policy
            user_permissions = await self.policy.get_user_permissions(user_id)
            
            # Check apakah user memiliki semua required permissions
            return required_permissions.issubset(user_permissions)
            
        except Exception as e:
            self.log_error(f"Permission check error: {str(e)}", exc=e)
            return False
    
    async def check_permission_bulk(self, user: Dict[str, Any], permission: str) -> bool:
        """
        Check single permission untuk user.
        
        Args:
            user: User data dictionary
            permission: Permission string
            
        Returns:
            True jika user memiliki permission
        """
        try:
            user_id = UUID(user['id'])
            user_permissions = await self.policy.get_user_permissions(user_id)
            return permission in user_permissions
            
        except Exception as e:
            self.log_error(f"Permission check error: {str(e)}", exc=e)
            return False
    
    async def assign_role(self, user_id: UUID, role_name: str) -> bool:
        """
        Assign role ke user.
        
        Args:
            user_id: User ID
            role_name: Role name
            
        Returns:
            True jika berhasil assign role
        """
        try:
            await self.policy.assign_user_role(user_id, role_name)
            self.log_info(f"Assigned role {role_name} to user {user_id}")
            return True
            
        except Exception as e:
            self.log_error(f"Role assignment error: {str(e)}", exc=e)
            return False
    
    async def revoke_role(self, user_id: UUID, role_name: str) -> bool:
        """
        Revoke role dari user.
        
        Args:
            user_id: User ID
            role_name: Role name
            
        Returns:
            True jika berhasil revoke role
        """
        try:
            await self.policy.revoke_user_role(user_id, role_name)
            self.log_info(f"Revoked role {role_name} from user {user_id}")
            return True
            
        except Exception as e:
            self.log_error(f"Role revocation error: {str(e)}", exc=e)
            return False
    
    def _extract_resource(self, request: Request) -> str:
        """
        Extract resource dari request path.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Resource string
        """
        path = request.url.path
        
        # Simple resource extraction dari path
        # /api/v1/users/123 -> users
        # /api/v1/products -> products
        path_parts = [p for p in path.split('/') if p]
        
        if len(path_parts) >= 3:  # /api/v1/resource
            return path_parts[2]
        elif len(path_parts) >= 1:
            return path_parts[0]
        
        return 'unknown'
    
    def _extract_action(self, request: Request) -> str:
        """
        Extract action dari request method.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Action string
        """
        method_mapping = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        
        return method_mapping.get(request.method.upper(), 'unknown')
    
    def _get_required_permissions(self, resource: str, action: str) -> Set[str]:
        """
        Get required permissions untuk resource dan action.
        
        Args:
            resource: Resource name
            action: Action name
            
        Returns:
            Set of required permissions
        """
        # Default permission format: resource:action
        base_permission = f"{resource}:{action}"
        
        # Get additional permissions dari config
        permission_mapping = self.get_config('permission_mapping', {})
        
        if base_permission in permission_mapping:
            return set(permission_mapping[base_permission])
        
        return {base_permission}

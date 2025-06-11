"""
Role-based Authentication middleware implementation.
Mengimplementasikan role-based access control untuk authentication.
"""
from typing import Optional, Dict, Any, List, Set
from fastapi import Request, HTTPException
from middleware.core.abstract.base_middleware import BaseMiddleware
from ..interfaces.auth_strategy import AuthStrategy, TokenData, AuthenticatedUser
from uuid import UUID


class RoleAuthStrategy(AuthStrategy):
    """
    Role-based Authentication Strategy.
    Mengimplementasikan role-based authentication dan authorization.
    """
    
    def __init__(self, role_hierarchy: Dict[str, List[str]] = None, permissions: Dict[str, List[str]] = None):
        """
        Initialize Role strategy.
        
        Args:
            role_hierarchy: Dictionary mapping roles ke parent roles
            permissions: Dictionary mapping roles ke permissions
        """
        self.role_hierarchy = role_hierarchy or {
            'super_admin': [],
            'admin': ['super_admin'],
            'manager': ['admin'],
            'user': ['manager'],
            'guest': ['user']
        }
        
        self.permissions = permissions or {
            'super_admin': ['*'],  # All permissions
            'admin': ['read', 'write', 'delete', 'manage_users'],
            'manager': ['read', 'write', 'manage_team'],
            'user': ['read', 'write_own'],
            'guest': ['read']
        }
        
        # Build effective permissions cache
        self._effective_permissions_cache = {}
        self._build_effective_permissions()
    
    def _build_effective_permissions(self) -> None:
        """Build effective permissions untuk setiap role berdasarkan hierarchy."""
        for role in self.role_hierarchy:
            self._effective_permissions_cache[role] = self._get_effective_permissions(role)
    
    def _get_effective_permissions(self, role: str) -> Set[str]:
        """Get effective permissions untuk role termasuk inherited permissions."""
        if role in self._effective_permissions_cache:
            return self._effective_permissions_cache[role]
        
        permissions = set(self.permissions.get(role, []))
        
        # Add permissions dari parent roles
        for parent_role in self.role_hierarchy.get(role, []):
            permissions.update(self._get_effective_permissions(parent_role))
        
        return permissions
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[AuthenticatedUser]:
        """
        Authenticate user dengan role validation.
        
        Args:
            credentials: Dictionary berisi user data dan roles
            
        Returns:
            AuthenticatedUser object atau None jika gagal
        """
        user_id = credentials.get('user_id')
        username = credentials.get('username')
        email = credentials.get('email')
        roles = credentials.get('roles', [])
        
        if not user_id or not username:
            return None
        
        # Validate roles
        valid_roles = self._validate_roles(roles)
        if not valid_roles:
            return None
        
        return AuthenticatedUser(
            id=UUID(user_id) if isinstance(user_id, str) else user_id,
            username=username,
            email=email or f"{username}@example.com",
            roles=valid_roles
        )
    
    async def create_token(self, user_id: UUID) -> TokenData:
        """
        Create token untuk role-based user.
        
        Args:
            user_id: User ID
            
        Returns:
            TokenData object
        """
        # Generate role-based token
        token = f"role_{user_id}_{hash(str(user_id)) % 1000000:06d}"
        
        return TokenData(
            access_token=token,
            token_type="role",
            expires_in=3600  # 1 hour
        )
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate role-based token.
        
        Args:
            token: Role token string
            
        Returns:
            User data dictionary atau None jika invalid
        """
        if not token.startswith('role_'):
            return None
        
        try:
            parts = token.split('_')
            if len(parts) < 3:
                return None
            
            user_id = parts[1]
            
            # TODO: Get actual user data dan roles dari database
            # Untuk sekarang, return mock data
            return {
                'id': user_id,
                'username': 'role_user',
                'email': 'role@example.com',
                'roles': ['user'],
                'permissions': list(self._effective_permissions_cache.get('user', set()))
            }
            
        except Exception:
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Refresh role-based token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New TokenData atau None jika gagal
        """
        if refresh_token.startswith('role_refresh_'):
            user_id_part = refresh_token.replace('role_refresh_', '').split('_')[0]
            try:
                user_id = UUID(user_id_part)
                return await self.create_token(user_id)
            except ValueError:
                return None
        
        return None
    
    def _validate_roles(self, roles: List[str]) -> List[str]:
        """Validate dan filter roles yang valid."""
        valid_roles = []
        for role in roles:
            if role in self.role_hierarchy:
                valid_roles.append(role)
        return valid_roles
    
    def has_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """
        Check apakah user dengan roles tertentu memiliki permission.
        
        Args:
            user_roles: List roles user
            required_permission: Permission yang dibutuhkan
            
        Returns:
            True jika user memiliki permission
        """
        for role in user_roles:
            permissions = self._effective_permissions_cache.get(role, set())
            if '*' in permissions or required_permission in permissions:
                return True
        return False
    
    def has_role(self, user_roles: List[str], required_role: str) -> bool:
        """
        Check apakah user memiliki role tertentu atau role yang lebih tinggi.
        
        Args:
            user_roles: List roles user
            required_role: Role yang dibutuhkan
            
        Returns:
            True jika user memiliki role
        """
        if required_role in user_roles:
            return True
        
        # Check role hierarchy
        for user_role in user_roles:
            if self._is_role_higher_or_equal(user_role, required_role):
                return True
        
        return False
    
    def _is_role_higher_or_equal(self, user_role: str, required_role: str) -> bool:
        """Check apakah user_role lebih tinggi atau sama dengan required_role."""
        if user_role == required_role:
            return True
        
        # Check if required_role is in user_role's hierarchy
        parent_roles = self.role_hierarchy.get(required_role, [])
        return user_role in parent_roles or any(
            self._is_role_higher_or_equal(user_role, parent) for parent in parent_roles
        )


class RoleMiddleware(BaseMiddleware):
    """
    Role-based Authentication Middleware.
    Menggunakan RoleAuthStrategy untuk role-based authentication dan authorization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Role middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.role_strategy: Optional[RoleAuthStrategy] = None
    
    def setup(self) -> None:
        """Setup Role strategy."""
        role_hierarchy = self.get_config('role_hierarchy', {})
        permissions = self.get_config('permissions', {})
        
        self.role_strategy = RoleAuthStrategy(
            role_hierarchy=role_hierarchy,
            permissions=permissions
        )
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process request untuk role-based authentication.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Modified request atau None jika ditolak
        """
        # Skip untuk public endpoints
        if self._is_public_endpoint(request):
            return request
        
        # Get user data dari request state (biasanya sudah di-set oleh auth middleware sebelumnya)
        user_data = getattr(request.state, 'user', None)
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="User not authenticated"
            )
        
        # Check role requirements untuk endpoint
        required_roles = self._get_required_roles(request)
        required_permissions = self._get_required_permissions(request)
        
        user_roles = user_data.get('roles', [])
        
        # Check role requirements
        if required_roles and not any(
            self.role_strategy.has_role(user_roles, role) for role in required_roles
        ):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient role. Required: {required_roles}"
            )
        
        # Check permission requirements
        if required_permissions and not any(
            self.role_strategy.has_permission(user_roles, perm) for perm in required_permissions
        ):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_permissions}"
            )
        
        # Add role info ke request state
        request.state.user_roles = user_roles
        request.state.user_permissions = []
        for role in user_roles:
            request.state.user_permissions.extend(
                list(self.role_strategy._effective_permissions_cache.get(role, set()))
            )
        
        return request
    
    def _get_required_roles(self, request: Request) -> List[str]:
        """Get required roles untuk endpoint."""
        # Check dari route metadata atau config
        endpoint_roles = self.get_config('endpoint_roles', {})
        path = request.url.path
        method = request.method.lower()
        
        # Check exact path match
        key = f"{method}:{path}"
        if key in endpoint_roles:
            return endpoint_roles[key]
        
        # Check pattern match
        for pattern, roles in endpoint_roles.items():
            if ':' in pattern:
                pattern_method, pattern_path = pattern.split(':', 1)
                if pattern_method == method and self._path_matches(path, pattern_path):
                    return roles
        
        return []
    
    def _get_required_permissions(self, request: Request) -> List[str]:
        """Get required permissions untuk endpoint."""
        endpoint_permissions = self.get_config('endpoint_permissions', {})
        path = request.url.path
        method = request.method.lower()
        
        # Check exact path match
        key = f"{method}:{path}"
        if key in endpoint_permissions:
            return endpoint_permissions[key]
        
        # Check pattern match
        for pattern, permissions in endpoint_permissions.items():
            if ':' in pattern:
                pattern_method, pattern_path = pattern.split(':', 1)
                if pattern_method == method and self._path_matches(path, pattern_path):
                    return permissions
        
        return []
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check apakah path matches dengan pattern."""
        if pattern.endswith('*'):
            return path.startswith(pattern[:-1])
        return path == pattern
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """Check apakah endpoint public."""
        public_paths = self.get_config('public_paths', ['/docs', '/openapi.json'])
        path = request.url.path
        
        return path in public_paths or any(
            path.startswith(p.rstrip('*')) for p in public_paths if p.endswith('*')
        )

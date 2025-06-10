"""
Authentication middleware menggunakan base middleware.
Mengikuti prinsip SOLID dan DRY.
"""
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from middleware.core.abstract.base_middleware import BaseMiddleware
from middleware.core.interfaces.middleware_interface import AuthenticationInterface
from .interfaces.auth_strategy import AuthStrategy

security = HTTPBearer()


class AuthMiddleware(BaseMiddleware, AuthenticationInterface):
    """
    Authentication middleware yang mengextend BaseMiddleware.
    Mengimplementasikan AuthenticationInterface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize authentication middleware.
        
        Args:
            config: Configuration dictionary yang harus berisi 'auth_strategy'
        """
        super().__init__(config)
        self.auth_strategy: Optional[AuthStrategy] = None
        
    def setup(self) -> None:
        """Setup authentication strategy dari config."""
        strategy_name = self.get_config('auth_strategy')
        if not strategy_name:
            raise ValueError("auth_strategy must be specified in config")
        
        # Get strategy from dependency container
        from middleware.core.registry.dependency_container import dependency_container
        self.auth_strategy = dependency_container.get_service(f"auth_strategy_{strategy_name}")
        
        if not self.auth_strategy:
            raise ValueError(f"Auth strategy '{strategy_name}' not found in dependency container")
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process incoming request untuk authentication.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Modified request dengan user info atau None jika ditolak
            
        Raises:
            HTTPException: Jika authentication gagal
        """
        try:
            # Skip authentication untuk public endpoints
            if self._is_public_endpoint(request):
                return request
            
            # Authenticate request
            is_authenticated = await self.authenticate(request)
            if not is_authenticated:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )
            
            return request
            
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(f"Authentication error: {str(e)}", exc=e)
            raise HTTPException(
                status_code=500,
                detail="Internal authentication error"
            )
    
    async def authenticate(self, request: Request) -> bool:
        """
        Authenticate request menggunakan strategy.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True jika authentication berhasil
        """
        try:
            # Get token from header
            credentials: HTTPAuthorizationCredentials = await security(request)
            if not credentials:
                return False
            
            # Validate token menggunakan strategy
            user = await self.auth_strategy.validate_token(credentials.credentials)
            if not user:
                return False
            
            # Add user to request state
            request.state.user = user
            request.state.token = credentials.credentials
            
            self.log_info(f"User authenticated: {user.get('id', 'unknown')}")
            return True
            
        except Exception as e:
            self.log_error(f"Authentication failed: {str(e)}", exc=e)
            return False
    
    async def get_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Get authenticated user dari request state.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            User data atau None jika tidak ada
        """
        return getattr(request.state, 'user', None)
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """
        Check apakah endpoint adalah public (tidak perlu auth).
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True jika endpoint public
        """
        public_paths = self.get_config('public_paths', [])
        path = request.url.path
        
        # Check exact match
        if path in public_paths:
            return True
        
        # Check pattern match
        for public_path in public_paths:
            if public_path.endswith('*'):
                prefix = public_path[:-1]
                if path.startswith(prefix):
                    return True
        
        return False

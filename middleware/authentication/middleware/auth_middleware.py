"""
Authentication middleware implementation.
Mengimplementasikan authentication middleware yang lebih lengkap dan mengikuti prinsip SOLID.
"""
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from middleware.core.abstract.base_middleware import BaseMiddleware
from middleware.core.interfaces.middleware_interface import AuthenticationInterface
from ..interfaces.auth_strategy import AuthStrategy, AuthenticatedUser
import logging

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseMiddleware, AuthenticationInterface):
    """
    Authentication middleware yang mengextend BaseMiddleware.
    Mengimplementasikan AuthenticationInterface dengan prinsip SOLID.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize authentication middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.auth_strategy: Optional[AuthStrategy] = None
        self.public_paths: list = []
        self.optional_auth_paths: list = []
        
    def setup(self) -> None:
        """Setup authentication middleware."""
        # Get configuration
        self.public_paths = self.get_config('public_paths', [
            '/docs', '/openapi.json', '/redoc', '/health'
        ])
        self.optional_auth_paths = self.get_config('optional_auth_paths', [])
        
        # Setup auth strategy
        strategy_config = self.get_config('strategy', {})
        strategy_type = strategy_config.get('type', 'jwt')
        
        if strategy_type == 'jwt':
            from ..strategies.jwt_strategy import JWTStrategy
            self.auth_strategy = JWTStrategy(strategy_config)
        elif strategy_type == 'api_key':
            from ..strategies.api_key_strategy import APIKeyStrategy
            self.auth_strategy = APIKeyStrategy(strategy_config)
        elif strategy_type == 'oauth2':
            from ..strategies.oauth2_strategy import OAuth2Strategy
            self.auth_strategy = OAuth2Strategy(strategy_config)
        else:
            raise ValueError(f"Unsupported auth strategy: {strategy_type}")
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process incoming request untuk authentication.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Modified request dengan user info atau None jika ditolak
        """
        try:
            path = request.url.path
            
            # Skip authentication untuk public endpoints
            if self._is_public_endpoint(path):
                return request
            
            # Optional authentication untuk beberapa endpoints
            is_optional = self._is_optional_auth_endpoint(path)
            
            # Get credentials
            credentials = await self._get_credentials(request)
            
            if not credentials and not is_optional:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication credentials required"
                )
            
            if credentials:
                # Authenticate request
                user_data = await self.authenticate(credentials.credentials)
                if user_data:
                    # Add user data ke request state
                    request.state.user = user_data
                    request.state.is_authenticated = True
                    request.state.token = credentials.credentials
                    
                    self.log_info(f"User authenticated: {user_data.get('username', 'unknown')}")
                elif not is_optional:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid authentication credentials"
                    )
            
            if not hasattr(request.state, 'is_authenticated'):
                request.state.is_authenticated = False
            
            return request
            
        except HTTPException:
            raise
        except Exception as e:
            self.log_error(f"Authentication error: {str(e)}", exc=e)
            raise HTTPException(
                status_code=500,
                detail="Internal authentication error"
            )
    
    async def process_response(self, request: Request, response: Response) -> Response:
        """
        Process response setelah authentication.
        
        Args:
            request: FastAPI Request object
            response: FastAPI Response object
            
        Returns:
            Modified response
        """
        # Add authentication headers jika diperlukan
        if hasattr(request.state, 'is_authenticated') and request.state.is_authenticated:
            response.headers["X-Authenticated"] = "true"
            if hasattr(request.state, 'user'):
                user = request.state.user
                response.headers["X-User-ID"] = str(user.get('id', ''))
        
        return response
    
    async def authenticate(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate token menggunakan strategy.
        
        Args:
            token: Authentication token
            
        Returns:
            User data dictionary atau None jika gagal
        """
        if not self.auth_strategy:
            raise RuntimeError("Auth strategy not configured")
        
        try:
            user_data = await self.auth_strategy.validate_token(token)
            return user_data
        except Exception as e:
            self.log_error(f"Token validation failed: {str(e)}", exc=e)
            return None
    
    async def get_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Get authenticated user dari request state.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            User data atau None jika tidak ada
        """
        return getattr(request.state, 'user', None)
    
    def is_authenticated(self, request: Request) -> bool:
        """
        Check apakah request sudah authenticated.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True jika authenticated
        """
        return getattr(request.state, 'is_authenticated', False)
    
    def require_auth(self, roles: Optional[list] = None, permissions: Optional[list] = None):
        """
        Decorator untuk require authentication dengan optional role/permission check.
        
        Args:
            roles: Required roles
            permissions: Required permissions
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            async def wrapper(request: Request, *args, **kwargs):
                if not self.is_authenticated(request):
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                user = await self.get_user(request)
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")
                
                # Check roles
                if roles:
                    user_roles = user.get('roles', [])
                    if not any(role in user_roles for role in roles):
                        raise HTTPException(
                            status_code=403, 
                            detail=f"Required roles: {roles}"
                        )
                
                # Check permissions
                if permissions:
                    user_permissions = user.get('permissions', [])
                    if not any(perm in user_permissions for perm in permissions):
                        raise HTTPException(
                            status_code=403, 
                            detail=f"Required permissions: {permissions}"
                        )
                
                return await func(request, *args, **kwargs)
            return wrapper
        return decorator
    
    async def _get_credentials(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Get credentials dari request."""
        try:
            return await security(request)
        except Exception:
            return None
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Check apakah endpoint adalah public."""
        return self._path_matches_patterns(path, self.public_paths)
    
    def _is_optional_auth_endpoint(self, path: str) -> bool:
        """Check apakah endpoint memiliki optional authentication."""
        return self._path_matches_patterns(path, self.optional_auth_paths)
    
    def _path_matches_patterns(self, path: str, patterns: list) -> bool:
        """Check apakah path matches dengan patterns."""
        for pattern in patterns:
            if pattern.endswith('*'):
                if path.startswith(pattern[:-1]):
                    return True
            elif pattern == path:
                return True
        return False


# Legacy compatibility class
class AuthMiddleware(AuthenticationMiddleware):
    """
    Legacy AuthMiddleware untuk backward compatibility.
    """
    
    def __init__(self, auth_service=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize dengan backward compatibility.
        
        Args:
            auth_service: Legacy auth service (deprecated)
            config: Configuration dictionary
        """
        if auth_service and not config:
            # Legacy mode
            logger.warning("Using legacy AuthMiddleware mode. Consider upgrading to AuthenticationMiddleware.")
            config = {'legacy_service': auth_service}
        
        super().__init__(config)
        self.auth_service = auth_service
    
    async def __call__(self, request: Request) -> Optional[Request]:
        """Legacy call method."""
        if self.auth_service:
            # Legacy behavior
            credentials = await security(request)
            if credentials:
                user_id = await self.auth_service.validate_token(credentials.credentials)
                if user_id:
                    request.state.user_id = user_id
            return request
        else:
            # New behavior
            return await self.process_request(request)

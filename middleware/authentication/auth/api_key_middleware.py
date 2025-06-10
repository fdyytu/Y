"""
API Key Authentication middleware implementation.
Mengimplementasikan API Key strategy untuk authentication.
"""
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from middleware.core.abstract.base_middleware import BaseMiddleware
from ..interfaces.auth_strategy import AuthStrategy, TokenData, AuthenticatedUser
from uuid import UUID


class APIKeyAuthStrategy(AuthStrategy):
    """
    API Key Authentication Strategy.
    Mengimplementasikan API Key authentication.
    """
    
    def __init__(self, valid_api_keys: Dict[str, Dict[str, Any]]):
        """
        Initialize API Key strategy.
        
        Args:
            valid_api_keys: Dictionary mapping API keys ke user data
        """
        self.valid_api_keys = valid_api_keys
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[AuthenticatedUser]:
        """
        Authenticate user dengan API key.
        
        Args:
            credentials: Dictionary berisi api_key
            
        Returns:
            AuthenticatedUser object atau None jika gagal
        """
        api_key = credentials.get('api_key')
        if not api_key or api_key not in self.valid_api_keys:
            return None
        
        user_data = self.valid_api_keys[api_key]
        return AuthenticatedUser(
            id=UUID(user_data['id']),
            username=user_data['username'],
            email=user_data['email'],
            roles=user_data.get('roles', [])
        )
    
    async def create_token(self, user_id: UUID) -> TokenData:
        """
        Create token untuk API key (return API key itself).
        
        Args:
            user_id: User ID
            
        Returns:
            TokenData object
        """
        # Find API key for this user
        for api_key, user_data in self.valid_api_keys.items():
            if user_data['id'] == str(user_id):
                return TokenData(
                    access_token=api_key,
                    token_type="apikey"
                )
        
        raise ValueError(f"No API key found for user {user_id}")
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key token.
        
        Args:
            token: API key string
            
        Returns:
            User data dictionary atau None jika invalid
        """
        if token in self.valid_api_keys:
            return self.valid_api_keys[token]
        return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Refresh token (API keys don't expire).
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Same TokenData (API keys don't change)
        """
        if refresh_token in self.valid_api_keys:
            return TokenData(
                access_token=refresh_token,
                token_type="apikey"
            )
        return None


class APIKeyMiddleware(BaseMiddleware):
    """
    API Key Authentication Middleware.
    Menggunakan APIKeyAuthStrategy untuk authentication.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize API Key middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.api_key_strategy: Optional[APIKeyAuthStrategy] = None
    
    def setup(self) -> None:
        """Setup API Key strategy."""
        # Get valid API keys dari config
        valid_api_keys = self.get_config('valid_api_keys', {
            'test-api-key-123': {
                'id': '12345678-1234-5678-1234-567812345678',
                'username': 'api_user',
                'email': 'api@example.com',
                'roles': ['api_user']
            }
        })
        
        self.api_key_strategy = APIKeyAuthStrategy(valid_api_keys)
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process request untuk API Key authentication.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Modified request atau None jika ditolak
        """
        # Skip untuk public endpoints
        if self._is_public_endpoint(request):
            return request
        
        # Get API key dari header atau query parameter
        api_key = self._extract_api_key(request)
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Missing API key"
            )
        
        # Validate API key
        user_data = await self.api_key_strategy.validate_token(api_key)
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        # Add user data ke request state
        request.state.user = user_data
        request.state.api_key = api_key
        
        return request
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """
        Extract API key dari request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            API key string atau None
        """
        # Check X-API-Key header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return api_key
        
        # Check Authorization header dengan Bearer
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        # Check query parameter
        api_key = request.query_params.get('api_key')
        if api_key:
            return api_key
        
        return None
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """Check apakah endpoint public."""
        public_paths = self.get_config('public_paths', ['/docs', '/openapi.json'])
        path = request.url.path
        
        return path in public_paths or any(
            path.startswith(p.rstrip('*')) for p in public_paths if p.endswith('*')
        )

"""
OAuth Authentication middleware implementation.
Mengimplementasikan OAuth 2.0 strategy untuk authentication.
"""
from typing import Optional, Dict, Any, List
import httpx
from fastapi import Request, HTTPException
from middleware.core.abstract.base_middleware import BaseMiddleware
from ..interfaces.auth_strategy import AuthStrategy, TokenData, AuthenticatedUser
from ..providers.google_provider import GoogleProvider
from ..providers.facebook_provider import FacebookProvider
from ..providers.apple_provider import AppleProvider
from uuid import UUID, uuid4


class OAuthAuthStrategy(AuthStrategy):
    """
    OAuth Authentication Strategy.
    Mengimplementasikan OAuth 2.0 authentication dengan berbagai provider.
    """
    
    def __init__(self, providers: Dict[str, Any]):
        """
        Initialize OAuth strategy.
        
        Args:
            providers: Dictionary berisi konfigurasi OAuth providers
        """
        self.providers = {}
        self._setup_providers(providers)
    
    def _setup_providers(self, providers_config: Dict[str, Any]) -> None:
        """Setup OAuth providers berdasarkan konfigurasi."""
        for provider_name, config in providers_config.items():
            if provider_name == 'google':
                self.providers['google'] = GoogleProvider(config)
            elif provider_name == 'facebook':
                self.providers['facebook'] = FacebookProvider(config)
            elif provider_name == 'apple':
                self.providers['apple'] = AppleProvider(config)
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[AuthenticatedUser]:
        """
        Authenticate user dengan OAuth provider.
        
        Args:
            credentials: Dictionary berisi provider dan access_token
            
        Returns:
            AuthenticatedUser object atau None jika gagal
        """
        provider_name = credentials.get('provider')
        access_token = credentials.get('access_token')
        
        if not provider_name or not access_token:
            return None
        
        provider = self.providers.get(provider_name)
        if not provider:
            return None
        
        # Get user info dari OAuth provider
        user_info = await provider.get_user_info(access_token)
        if not user_info:
            return None
        
        # Convert ke AuthenticatedUser
        return AuthenticatedUser(
            id=UUID(user_info.get('id', str(uuid4()))),
            username=user_info.get('username', user_info.get('email', '')),
            email=user_info.get('email', ''),
            roles=user_info.get('roles', ['user']),
            provider=provider_name,
            provider_id=user_info.get('provider_id')
        )
    
    async def create_token(self, user_id: UUID) -> TokenData:
        """
        Create token untuk OAuth user.
        
        Args:
            user_id: User ID
            
        Returns:
            TokenData object
        """
        # Untuk OAuth, kita bisa generate internal token
        # atau menggunakan provider token
        internal_token = f"oauth_{user_id}_{uuid4().hex[:16]}"
        
        return TokenData(
            access_token=internal_token,
            token_type="oauth",
            expires_in=3600  # 1 hour
        )
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate OAuth token.
        
        Args:
            token: OAuth token string
            
        Returns:
            User data dictionary atau None jika invalid
        """
        # Parse internal OAuth token
        if not token.startswith('oauth_'):
            return None
        
        try:
            parts = token.split('_')
            if len(parts) < 3:
                return None
            
            user_id = parts[1]
            
            # TODO: Get actual user data dari database
            # Untuk sekarang, return mock data
            return {
                'id': user_id,
                'username': 'oauth_user',
                'email': 'oauth@example.com',
                'roles': ['user'],
                'provider': 'oauth'
            }
            
        except Exception:
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Refresh OAuth token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New TokenData atau None jika gagal
        """
        # OAuth refresh logic tergantung provider
        # Untuk sekarang, generate token baru
        if refresh_token.startswith('oauth_refresh_'):
            user_id_part = refresh_token.replace('oauth_refresh_', '').split('_')[0]
            try:
                user_id = UUID(user_id_part)
                return await self.create_token(user_id)
            except ValueError:
                return None
        
        return None
    
    def get_authorization_url(self, provider_name: str, redirect_uri: str, state: str = None) -> str:
        """
        Get authorization URL untuk OAuth flow.
        
        Args:
            provider_name: Nama provider
            redirect_uri: Redirect URI
            state: State parameter untuk security
            
        Returns:
            Authorization URL
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' tidak tersedia")
        
        return provider.get_authorization_url(redirect_uri, state)
    
    async def exchange_code_for_token(self, provider_name: str, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code untuk access token.
        
        Args:
            provider_name: Nama provider
            code: Authorization code
            redirect_uri: Redirect URI
            
        Returns:
            Token data atau None jika gagal
        """
        provider = self.providers.get(provider_name)
        if not provider:
            return None
        
        return await provider.exchange_code_for_token(code, redirect_uri)


class OAuthMiddleware(BaseMiddleware):
    """
    OAuth Authentication Middleware.
    Menggunakan OAuthAuthStrategy untuk authentication.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OAuth middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.oauth_strategy: Optional[OAuthAuthStrategy] = None
    
    def setup(self) -> None:
        """Setup OAuth strategy."""
        providers_config = self.get_config('providers', {
            'google': {
                'client_id': 'your-google-client-id',
                'client_secret': 'your-google-client-secret',
                'scope': ['openid', 'email', 'profile']
            }
        })
        
        self.oauth_strategy = OAuthAuthStrategy(providers_config)
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process request untuk OAuth authentication.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Modified request atau None jika ditolak
        """
        # Skip untuk public endpoints
        if self._is_public_endpoint(request):
            return request
        
        # Get token dari Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Missing authorization header"
            )
        
        # Support berbagai format token
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        elif auth_header.startswith('OAuth '):
            token = auth_header.split(' ')[1]
        else:
            token = auth_header
        
        # Validate token
        user_data = await self.oauth_strategy.validate_token(token)
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid OAuth token"
            )
        
        # Add user data ke request state
        request.state.user = user_data
        request.state.oauth_token = token
        
        return request
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """Check apakah endpoint public."""
        public_paths = self.get_config('public_paths', [
            '/auth/oauth/login',
            '/auth/oauth/callback',
            '/docs',
            '/openapi.json'
        ])
        path = request.url.path
        
        return path in public_paths or any(
            path.startswith(p.rstrip('*')) for p in public_paths if p.endswith('*')
        )
    
    def get_authorization_url(self, provider: str, redirect_uri: str, state: str = None) -> str:
        """
        Get authorization URL untuk OAuth flow.
        
        Args:
            provider: Nama provider
            redirect_uri: Redirect URI
            state: State parameter
            
        Returns:
            Authorization URL
        """
        if not self.oauth_strategy:
            raise RuntimeError("OAuth strategy belum di-setup")
        
        return self.oauth_strategy.get_authorization_url(provider, redirect_uri, state)
    
    async def handle_callback(self, provider: str, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """
        Handle OAuth callback.
        
        Args:
            provider: Nama provider
            code: Authorization code
            redirect_uri: Redirect URI
            
        Returns:
            Token data atau None jika gagal
        """
        if not self.oauth_strategy:
            raise RuntimeError("OAuth strategy belum di-setup")
        
        return await self.oauth_strategy.exchange_code_for_token(provider, code, redirect_uri)

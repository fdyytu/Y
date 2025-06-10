"""
JWT Authentication middleware implementation.
Mengimplementasikan JWT strategy untuk authentication.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from fastapi import Request, HTTPException
from middleware.core.abstract.base_middleware import BaseMiddleware
from ..interfaces.auth_strategy import AuthStrategy, TokenData, AuthenticatedUser
from uuid import UUID


class JWTAuthStrategy(AuthStrategy):
    """
    JWT Authentication Strategy.
    Mengimplementasikan JWT token authentication.
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256", expire_minutes: int = 30):
        """
        Initialize JWT strategy.
        
        Args:
            secret_key: Secret key untuk JWT signing
            algorithm: JWT algorithm (default: HS256)
            expire_minutes: Token expiration time dalam menit
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes
    
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[AuthenticatedUser]:
        """
        Authenticate user dengan username/password.
        
        Args:
            credentials: Dictionary berisi username dan password
            
        Returns:
            AuthenticatedUser object atau None jika gagal
        """
        username = credentials.get('username')
        password = credentials.get('password')
        
        if not username or not password:
            return None
        
        # TODO: Implement actual user validation dari database
        # Untuk sekarang, contoh sederhana
        if username == "admin" and password == "password":
            return AuthenticatedUser(
                id=UUID('12345678-1234-5678-1234-567812345678'),
                username=username,
                email=f"{username}@example.com",
                roles=['admin']
            )
        
        return None
    
    async def create_token(self, user_id: UUID) -> TokenData:
        """
        Create JWT token untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            TokenData object
        """
        # Create token payload
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        payload = {
            'user_id': str(user_id),
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        # Encode JWT token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return TokenData(
            access_token=token,
            token_type="bearer",
            expires_in=self.expire_minutes * 60
        )
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User data dictionary atau None jika invalid
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is expired
            if self.is_token_expired(payload):
                return None
            
            # Get user data
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            # TODO: Get actual user data dari database
            # Untuk sekarang, return mock data
            return {
                'id': user_id,
                'username': 'admin',
                'email': 'admin@example.com',
                'roles': ['admin']
            }
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[TokenData]:
        """
        Refresh JWT token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New TokenData atau None jika gagal
        """
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if it's a refresh token
            if payload.get('type') != 'refresh':
                return None
            
            # Get user ID
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            # Create new access token
            return await self.create_token(UUID(user_id))
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def create_refresh_token(self, user_id: UUID) -> str:
        """
        Create refresh token untuk user.
        
        Args:
            user_id: User ID
            
        Returns:
            Refresh token string
        """
        # Refresh token expires in 7 days
        expire = datetime.utcnow() + timedelta(days=7)
        payload = {
            'user_id': str(user_id),
            'exp': expire,
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


class JWTMiddleware(BaseMiddleware):
    """
    JWT Authentication Middleware.
    Menggunakan JWTAuthStrategy untuk authentication.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize JWT middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.jwt_strategy: Optional[JWTAuthStrategy] = None
    
    def setup(self) -> None:
        """Setup JWT strategy."""
        secret_key = self.get_config('secret_key', 'your-secret-key')
        algorithm = self.get_config('algorithm', 'HS256')
        expire_minutes = self.get_config('expire_minutes', 30)
        
        self.jwt_strategy = JWTAuthStrategy(
            secret_key=secret_key,
            algorithm=algorithm,
            expire_minutes=expire_minutes
        )
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process request untuk JWT authentication.
        
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
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header.split(' ')[1]
        
        # Validate token
        user_data = await self.jwt_strategy.validate_token(token)
        if not user_data:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )
        
        # Add user data ke request state
        request.state.user = user_data
        request.state.token = token
        
        return request
    
    def _is_public_endpoint(self, request: Request) -> bool:
        """Check apakah endpoint public."""
        public_paths = self.get_config('public_paths', ['/auth/login', '/auth/register'])
        path = request.url.path
        
        return path in public_paths or any(
            path.startswith(p.rstrip('*')) for p in public_paths if p.endswith('*')
        )

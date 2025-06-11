"""
Rate Limiting middleware implementation.
Mengimplementasikan rate limiting dengan berbagai strategi.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from fastapi import Request, HTTPException
from middleware.core.abstract.base_middleware import BaseMiddleware
from middleware.core.interfaces.middleware_interface import RateLimitInterface


class TokenBucketRateLimiter:
    """
    Token Bucket algorithm untuk rate limiting.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum tokens dalam bucket
            refill_rate: Rate untuk refill tokens per detik
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = datetime.utcnow()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens dari bucket.
        
        Args:
            tokens: Jumlah tokens yang akan dikonsumsi
            
        Returns:
            True jika berhasil consume tokens
        """
        async with self._lock:
            await self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def _refill(self) -> None:
        """Refill tokens berdasarkan waktu yang berlalu."""
        now = datetime.utcnow()
        time_passed = (now - self.last_refill).total_seconds()
        
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    async def get_remaining_tokens(self) -> int:
        """Get jumlah tokens yang tersisa."""
        async with self._lock:
            await self._refill()
            return int(self.tokens)


class SlidingWindowRateLimiter:
    """
    Sliding Window algorithm untuk rate limiting.
    """
    
    def __init__(self, limit: int, window_seconds: int):
        """
        Initialize sliding window.
        
        Args:
            limit: Maximum requests dalam window
            window_seconds: Window size dalam detik
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, identifier: str) -> bool:
        """
        Check apakah request diizinkan.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            
        Returns:
            True jika request diizinkan
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # Initialize if not exists
            if identifier not in self.requests:
                self.requests[identifier] = []
            
            # Clean old requests
            cutoff_time = now - timedelta(seconds=self.window_seconds)
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff_time
            ]
            
            # Check limit
            if len(self.requests[identifier]) >= self.limit:
                return False
            
            # Add current request
            self.requests[identifier].append(now)
            return True
    
    async def get_remaining(self, identifier: str) -> int:
        """Get remaining requests untuk identifier."""
        async with self._lock:
            if identifier not in self.requests:
                return self.limit
            
            # Clean old requests
            now = datetime.utcnow()
            cutoff_time = now - timedelta(seconds=self.window_seconds)
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff_time
            ]
            
            return max(0, self.limit - len(self.requests[identifier]))


class RateLimitMiddleware(BaseMiddleware, RateLimitInterface):
    """
    Rate Limiting middleware.
    Mengimplementasikan rate limiting dengan berbagai algoritma.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize rate limit middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.limiters: Dict[str, Any] = {}
        self.global_limiter: Optional[Any] = None
    
    def setup(self) -> None:
        """Setup rate limiters."""
        algorithm = self.get_config('algorithm', 'token_bucket')
        
        if algorithm == 'token_bucket':
            capacity = self.get_config('capacity', 100)
            refill_rate = self.get_config('refill_rate', 10.0)
            self.global_limiter = TokenBucketRateLimiter(capacity, refill_rate)
        
        elif algorithm == 'sliding_window':
            limit = self.get_config('limit', 100)
            window_seconds = self.get_config('window_seconds', 60)
            self.global_limiter = SlidingWindowRateLimiter(limit, window_seconds)
        
        else:
            raise ValueError(f"Unsupported rate limiting algorithm: {algorithm}")
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process request untuk rate limiting.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Request jika diizinkan
            
        Raises:
            HTTPException: Jika rate limit exceeded
        """
        # Skip untuk public endpoints yang dikecualikan
        if self._is_excluded_endpoint(request):
            return request
        
        # Get identifier untuk rate limiting
        identifier = await self._get_identifier(request)
        
        # Check rate limit
        is_allowed = await self.is_allowed(identifier)
        if not is_allowed:
            remaining = await self.get_remaining(identifier)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(self._get_reset_time())
                }
            )
        
        # Add rate limit headers
        remaining = await self.get_remaining(identifier)
        request.state.rate_limit_remaining = remaining
        
        return request
    
    async def is_allowed(self, identifier: str) -> bool:
        """
        Check apakah request diizinkan untuk identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            True jika diizinkan
        """
        if isinstance(self.global_limiter, TokenBucketRateLimiter):
            return await self.global_limiter.consume()
        elif isinstance(self.global_limiter, SlidingWindowRateLimiter):
            return await self.global_limiter.is_allowed(identifier)
        
        return True
    
    async def get_remaining(self, identifier: str) -> int:
        """
        Get remaining requests untuk identifier.
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Jumlah remaining requests
        """
        if isinstance(self.global_limiter, TokenBucketRateLimiter):
            return await self.global_limiter.get_remaining_tokens()
        elif isinstance(self.global_limiter, SlidingWindowRateLimiter):
            return await self.global_limiter.get_remaining(identifier)
        
        return 0
    
    async def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier untuk rate limiting.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Unique identifier string
        """
        # Priority: User ID > API Key > IP Address
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.get('id', 'unknown')}"
        
        # Check for API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"api_key:{api_key}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _is_excluded_endpoint(self, request: Request) -> bool:
        """Check apakah endpoint dikecualikan dari rate limiting."""
        excluded_paths = self.get_config('excluded_paths', [])
        path = request.url.path
        
        return path in excluded_paths or any(
            path.startswith(p.rstrip('*')) for p in excluded_paths if p.endswith('*')
        )
    
    def _get_reset_time(self) -> int:
        """Get reset time untuk rate limit."""
        window_seconds = self.get_config('window_seconds', 60)
        return int((datetime.utcnow() + timedelta(seconds=window_seconds)).timestamp())

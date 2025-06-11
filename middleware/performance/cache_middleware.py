"""
Cache middleware implementation.
Mengimplementasikan caching dengan berbagai strategi.
"""
from typing import Optional, Dict, Any, Union
import json
import hashlib
from datetime import datetime, timedelta
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from middleware.core.abstract.base_middleware import BaseMiddleware
from middleware.core.interfaces.middleware_interface import CacheInterface


class InMemoryCache:
    """
    Simple in-memory cache implementation.
    """
    
    def __init__(self):
        """Initialize in-memory cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value dari cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value atau None jika tidak ada/expired
        """
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        
        # Check expiration
        if cache_entry.get('expires_at'):
            if datetime.utcnow() > cache_entry['expires_at']:
                del self._cache[key]
                return None
        
        return cache_entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value ke cache.
        
        Args:
            key: Cache key
            value: Value yang akan di-cache
            ttl: Time to live dalam detik
            
        Returns:
            True jika berhasil set
        """
        cache_entry = {
            'value': value,
            'created_at': datetime.utcnow()
        }
        
        if ttl:
            cache_entry['expires_at'] = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = cache_entry
        return True
    
    async def delete(self, key: str) -> bool:
        """
        Delete value dari cache.
        
        Args:
            key: Cache key
            
        Returns:
            True jika berhasil delete
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear semua cache."""
        self._cache.clear()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'total_keys': len(self._cache),
            'memory_usage': len(str(self._cache))  # Rough estimate
        }


class RedisCache:
    """
    Redis cache implementation (placeholder).
    Implementasi actual memerlukan redis client.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        self.host = host
        self.port = port
        self.db = db
        # TODO: Initialize actual redis client
        self._redis = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value dari Redis cache."""
        # TODO: Implement actual Redis get
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value ke Redis cache."""
        # TODO: Implement actual Redis set
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value dari Redis cache."""
        # TODO: Implement actual Redis delete
        return True


class CacheMiddleware(BaseMiddleware, CacheInterface):
    """
    Cache middleware untuk HTTP response caching.
    Mengimplementasikan response caching dengan berbagai strategi.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.cache_backend: Union[InMemoryCache, RedisCache] = None
        self.default_ttl: int = 300  # 5 minutes
    
    def setup(self) -> None:
        """Setup cache backend."""
        backend_type = self.get_config('backend', 'memory')
        self.default_ttl = self.get_config('default_ttl', 300)
        
        if backend_type == 'memory':
            self.cache_backend = InMemoryCache()
        elif backend_type == 'redis':
            redis_config = self.get_config('redis', {})
            self.cache_backend = RedisCache(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0)
            )
        else:
            raise ValueError(f"Unsupported cache backend: {backend_type}")
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process request untuk cache lookup.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Request object atau cached response
        """
        # Skip caching untuk non-GET requests
        if request.method != 'GET':
            return request
        
        # Skip untuk endpoints yang dikecualikan
        if self._is_excluded_endpoint(request):
            return request
        
        # Generate cache key
        cache_key = await self._generate_cache_key(request)
        
        # Try to get cached response
        cached_response = await self.get(cache_key)
        if cached_response:
            self.log_info(f"Cache hit for key: {cache_key}")
            
            # Return cached response
            response_data = json.loads(cached_response)
            return JSONResponse(
                content=response_data['content'],
                status_code=response_data['status_code'],
                headers={
                    **response_data.get('headers', {}),
                    'X-Cache': 'HIT',
                    'X-Cache-Key': cache_key
                }
            )
        
        # Cache miss - add cache key to request state
        request.state.cache_key = cache_key
        self.log_info(f"Cache miss for key: {cache_key}")
        
        return request
    
    async def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """
        Process response untuk caching.
        
        Args:
            request: FastAPI Request object
            response: FastAPI Response object
            
        Returns:
            Modified response dengan cache headers
        """
        # Skip jika tidak ada cache key (non-cacheable request)
        cache_key = getattr(request.state, 'cache_key', None)
        if not cache_key:
            return response
        
        # Skip caching untuk error responses
        if response.status_code >= 400:
            return response
        
        # Skip jika response sudah dari cache
        if response.headers.get('X-Cache') == 'HIT':
            return response
        
        try:
            # Get response content
            if hasattr(response, 'body'):
                content = response.body.decode('utf-8')
            else:
                content = ""
            
            # Prepare cache data
            cache_data = {
                'content': json.loads(content) if content else {},
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
            
            # Get TTL untuk endpoint ini
            ttl = self._get_endpoint_ttl(request)
            
            # Cache the response
            await self.set(cache_key, json.dumps(cache_data), ttl)
            
            # Add cache headers
            response.headers['X-Cache'] = 'MISS'
            response.headers['X-Cache-Key'] = cache_key
            response.headers['Cache-Control'] = f'max-age={ttl}'
            
            self.log_info(f"Response cached with key: {cache_key}, TTL: {ttl}")
            
        except Exception as e:
            self.log_error(f"Failed to cache response: {str(e)}", exc=e)
        
        return response
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value dari cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value atau None
        """
        return await self.cache_backend.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value ke cache.
        
        Args:
            key: Cache key
            value: Value yang akan di-cache
            ttl: Time to live dalam detik
            
        Returns:
            True jika berhasil
        """
        if ttl is None:
            ttl = self.default_ttl
        
        return await self.cache_backend.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """
        Delete value dari cache.
        
        Args:
            key: Cache key
            
        Returns:
            True jika berhasil
        """
        return await self.cache_backend.delete(key)
    
    async def _generate_cache_key(self, request: Request) -> str:
        """
        Generate cache key untuk request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Cache key string
        """
        # Base key components
        key_components = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        
        # Add user-specific caching jika diperlukan
        if self.get_config('user_specific_cache', False):
            user_id = getattr(request.state, 'user', {}).get('id', 'anonymous')
            key_components.append(f"user:{user_id}")
        
        # Add custom headers yang mempengaruhi response
        cache_headers = self.get_config('cache_headers', [])
        for header in cache_headers:
            header_value = request.headers.get(header, '')
            key_components.append(f"{header}:{header_value}")
        
        # Create hash dari components
        key_string = '|'.join(key_components)
        cache_key = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"cache:{cache_key}"
    
    def _is_excluded_endpoint(self, request: Request) -> bool:
        """Check apakah endpoint dikecualikan dari caching."""
        excluded_paths = self.get_config('excluded_paths', [])
        path = request.url.path
        
        return path in excluded_paths or any(
            path.startswith(p.rstrip('*')) for p in excluded_paths if p.endswith('*')
        )
    
    def _get_endpoint_ttl(self, request: Request) -> int:
        """
        Get TTL untuk specific endpoint.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            TTL dalam detik
        """
        endpoint_ttls = self.get_config('endpoint_ttls', {})
        path = request.url.path
        
        # Check exact match
        if path in endpoint_ttls:
            return endpoint_ttls[path]
        
        # Check pattern match
        for pattern, ttl in endpoint_ttls.items():
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                if path.startswith(prefix):
                    return ttl
        
        return self.default_ttl

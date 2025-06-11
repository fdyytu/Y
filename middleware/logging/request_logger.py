"""
Request logging middleware implementation.
Mengimplementasikan logging untuk semua HTTP requests dan responses.
"""
from typing import Optional, Dict, Any
import time
import json
from datetime import datetime
from fastapi import Request, Response
from middleware.core.abstract.base_middleware import BaseMiddleware
from middleware.core.interfaces.middleware_interface import LoggingInterface


class RequestLoggerMiddleware(BaseMiddleware, LoggingInterface):
    """
    Request Logger middleware untuk logging HTTP requests dan responses.
    Mengimplementasikan LoggingInterface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize request logger middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.log_requests: bool = True
        self.log_responses: bool = True
        self.log_headers: bool = False
        self.log_body: bool = False
        self.excluded_paths: list = []
    
    def setup(self) -> None:
        """Setup logging configuration."""
        self.log_requests = self.get_config('log_requests', True)
        self.log_responses = self.get_config('log_responses', True)
        self.log_headers = self.get_config('log_headers', False)
        self.log_body = self.get_config('log_body', False)
        self.excluded_paths = self.get_config('excluded_paths', ['/health', '/metrics'])
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process incoming request untuk logging.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Request object dengan timestamp
        """
        # Skip logging untuk excluded paths
        if self._is_excluded_path(request):
            return request
        
        # Add start time ke request state
        request.state.start_time = time.time()
        request.state.request_id = self._generate_request_id()
        
        # Log incoming request
        if self.log_requests:
            await self.log_request(request)
        
        return request
    
    async def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """
        Process outgoing response untuk logging.
        
        Args:
            request: FastAPI Request object
            response: FastAPI Response object
            
        Returns:
            Response object dengan logging headers
        """
        # Skip logging untuk excluded paths
        if self._is_excluded_path(request):
            return response
        
        # Log outgoing response
        if self.log_responses:
            await self.log_response(request, response)
        
        # Add request ID ke response headers
        if hasattr(request.state, 'request_id'):
            response.headers['X-Request-ID'] = request.state.request_id
        
        return response
    
    async def log_request(self, request: Request) -> None:
        """
        Log incoming request.
        
        Args:
            request: FastAPI Request object
        """
        try:
            # Basic request info
            log_data = {
                'type': 'request',
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': getattr(request.state, 'request_id', 'unknown'),
                'method': request.method,
                'url': str(request.url),
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'client_ip': self._get_client_ip(request),
                'user_agent': request.headers.get('user-agent', 'unknown')
            }
            
            # Add user info jika tersedia
            if hasattr(request.state, 'user') and request.state.user:
                log_data['user_id'] = request.state.user.get('id', 'unknown')
                log_data['username'] = request.state.user.get('username', 'unknown')
            
            # Add headers jika enabled
            if self.log_headers:
                log_data['headers'] = dict(request.headers)
            
            # Add body jika enabled dan method yang sesuai
            if self.log_body and request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    body = await request.body()
                    if body:
                        # Try to parse as JSON
                        try:
                            log_data['body'] = json.loads(body.decode('utf-8'))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            log_data['body'] = body.decode('utf-8', errors='ignore')[:1000]  # Limit size
                except Exception:
                    log_data['body'] = 'Unable to read body'
            
            # Log the request
            self.log_info(f"HTTP Request: {request.method} {request.url.path}", **log_data)
            
        except Exception as e:
            self.log_error(f"Failed to log request: {str(e)}", exc=e)
    
    async def log_response(self, request: Request, response: Response) -> None:
        """
        Log outgoing response.
        
        Args:
            request: FastAPI Request object
            response: FastAPI Response object
        """
        try:
            # Calculate response time
            start_time = getattr(request.state, 'start_time', time.time())
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Basic response info
            log_data = {
                'type': 'response',
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': getattr(request.state, 'request_id', 'unknown'),
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'content_length': response.headers.get('content-length', 'unknown')
            }
            
            # Add user info jika tersedia
            if hasattr(request.state, 'user') and request.state.user:
                log_data['user_id'] = request.state.user.get('id', 'unknown')
            
            # Add headers jika enabled
            if self.log_headers:
                log_data['response_headers'] = dict(response.headers)
            
            # Add response body jika enabled dan status code tertentu
            if self.log_body and response.status_code >= 400:
                try:
                    if hasattr(response, 'body'):
                        body = response.body
                        if body:
                            try:
                                log_data['response_body'] = json.loads(body.decode('utf-8'))
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                log_data['response_body'] = body.decode('utf-8', errors='ignore')[:1000]
                except Exception:
                    log_data['response_body'] = 'Unable to read response body'
            
            # Determine log level berdasarkan status code
            if response.status_code >= 500:
                self.log_error(f"HTTP Response: {request.method} {request.url.path} - {response.status_code}", **log_data)
            elif response.status_code >= 400:
                self.log_warning(f"HTTP Response: {request.method} {request.url.path} - {response.status_code}", **log_data)
            else:
                self.log_info(f"HTTP Response: {request.method} {request.url.path} - {response.status_code}", **log_data)
            
        except Exception as e:
            self.log_error(f"Failed to log response: {str(e)}", exc=e)
    
    def _is_excluded_path(self, request: Request) -> bool:
        """
        Check apakah path dikecualikan dari logging.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True jika path dikecualikan
        """
        path = request.url.path
        
        for excluded_path in self.excluded_paths:
            if excluded_path.endswith('*'):
                # Wildcard match
                prefix = excluded_path[:-1]
                if path.startswith(prefix):
                    return True
            else:
                # Exact match
                if path == excluded_path:
                    return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address dari request.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if request.client:
            return request.client.host
        
        return 'unknown'
    
    def _generate_request_id(self) -> str:
        """
        Generate unique request ID.
        
        Returns:
            Unique request ID string
        """
        import uuid
        return str(uuid.uuid4())[:8]  # Short UUID untuk readability

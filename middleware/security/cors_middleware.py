"""
CORS (Cross-Origin Resource Sharing) middleware implementation.
Menggunakan base middleware dan mengikuti prinsip SOLID.
"""
from typing import Optional, Dict, Any, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from middleware.core.abstract.base_middleware import BaseMiddleware
from middleware.core.interfaces.middleware_interface import SecurityInterface


class CORSMiddleware(BaseMiddleware, SecurityInterface):
    """
    CORS middleware yang mengextend BaseMiddleware.
    Mengimplementasikan SecurityInterface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CORS middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.allowed_origins: List[str] = []
        self.allowed_methods: List[str] = []
        self.allowed_headers: List[str] = []
        self.allow_credentials: bool = False
        self.max_age: int = 600
    
    def setup(self) -> None:
        """Setup CORS configuration."""
        self.allowed_origins = self.get_config('allowed_origins', ['*'])
        self.allowed_methods = self.get_config('allowed_methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        self.allowed_headers = self.get_config('allowed_headers', ['*'])
        self.allow_credentials = self.get_config('allow_credentials', False)
        self.max_age = self.get_config('max_age', 600)
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process incoming request untuk CORS.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Modified request atau preflight response
        """
        origin = request.headers.get('origin')
        
        # Handle preflight request
        if request.method == 'OPTIONS':
            return await self._handle_preflight(request, origin)
        
        # Validate origin untuk actual request
        if not self._is_origin_allowed(origin):
            self.log_warning(f"CORS: Origin not allowed: {origin}")
            # Biarkan request lanjut tapi tidak akan ada CORS headers
        
        return request
    
    async def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """
        Process outgoing response untuk menambah CORS headers.
        
        Args:
            request: FastAPI Request object
            response: FastAPI Response object
            
        Returns:
            Modified response dengan CORS headers
        """
        origin = request.headers.get('origin')
        
        if self._is_origin_allowed(origin):
            # Add CORS headers
            response.headers['Access-Control-Allow-Origin'] = origin or '*'
            
            if self.allow_credentials:
                response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            # Add vary header untuk caching
            response.headers['Vary'] = 'Origin'
        
        return response
    
    async def validate_request(self, request: Request) -> bool:
        """
        Validate request security untuk CORS.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            True jika request valid
        """
        origin = request.headers.get('origin')
        
        # Allow requests without origin (same-origin atau non-browser)
        if not origin:
            return True
        
        return self._is_origin_allowed(origin)
    
    async def sanitize_input(self, data: Any) -> Any:
        """
        Sanitize input data (tidak diperlukan untuk CORS).
        
        Args:
            data: Input data
            
        Returns:
            Sanitized data
        """
        return data
    
    async def _handle_preflight(self, request: Request, origin: Optional[str]) -> Response:
        """
        Handle CORS preflight request.
        
        Args:
            request: FastAPI Request object
            origin: Request origin
            
        Returns:
            Preflight response
        """
        if not self._is_origin_allowed(origin):
            self.log_warning(f"CORS preflight: Origin not allowed: {origin}")
            return JSONResponse(
                status_code=403,
                content={"error": "CORS: Origin not allowed"}
            )
        
        # Get requested method dan headers
        requested_method = request.headers.get('access-control-request-method')
        requested_headers = request.headers.get('access-control-request-headers', '')
        
        # Validate requested method
        if requested_method and not self._is_method_allowed(requested_method):
            self.log_warning(f"CORS preflight: Method not allowed: {requested_method}")
            return JSONResponse(
                status_code=405,
                content={"error": "CORS: Method not allowed"}
            )
        
        # Create preflight response
        response = JSONResponse(status_code=200, content={})
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = origin or '*'
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
        response.headers['Access-Control-Max-Age'] = str(self.max_age)
        
        if self.allow_credentials:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        self.log_info(f"CORS preflight handled for origin: {origin}")
        return response
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """
        Check apakah origin diizinkan.
        
        Args:
            origin: Request origin
            
        Returns:
            True jika origin diizinkan
        """
        if not origin:
            return True
        
        # Allow all origins
        if '*' in self.allowed_origins:
            return True
        
        # Check exact match
        if origin in self.allowed_origins:
            return True
        
        # Check wildcard patterns
        for allowed_origin in self.allowed_origins:
            if allowed_origin.startswith('*.'):
                domain = allowed_origin[2:]  # Remove *.
                if origin.endswith(domain):
                    return True
        
        return False
    
    def _is_method_allowed(self, method: str) -> bool:
        """
        Check apakah HTTP method diizinkan.
        
        Args:
            method: HTTP method
            
        Returns:
            True jika method diizinkan
        """
        return method.upper() in [m.upper() for m in self.allowed_methods]
    
    def _is_header_allowed(self, header: str) -> bool:
        """
        Check apakah header diizinkan.
        
        Args:
            header: Header name
            
        Returns:
            True jika header diizinkan
        """
        if '*' in self.allowed_headers:
            return True
        
        return header.lower() in [h.lower() for h in self.allowed_headers]

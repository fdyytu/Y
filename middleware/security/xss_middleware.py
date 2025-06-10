"""
XSS (Cross-Site Scripting) protection middleware implementation.
Menggunakan base middleware dan mengikuti prinsip SOLID.
"""
from typing import Optional, Dict, Any, List
import re
import html
from fastapi import Request, Response, HTTPException
from middleware.core.abstract.base_middleware import BaseMiddleware
from middleware.core.interfaces.middleware_interface import SecurityInterface


class XSSMiddleware(BaseMiddleware, SecurityInterface):
    """
    XSS protection middleware yang mengextend BaseMiddleware.
    Mengimplementasikan SecurityInterface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize XSS middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.auto_escape: bool = True
        self.block_suspicious: bool = True
        self.allowed_tags: List[str] = []
        self.xss_patterns: List[re.Pattern] = []
    
    def setup(self) -> None:
        """Setup XSS protection configuration."""
        self.auto_escape = self.get_config('auto_escape', True)
        self.block_suspicious = self.get_config('block_suspicious', True)
        self.allowed_tags = self.get_config('allowed_tags', [])
        
        # Compile XSS detection patterns
        patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>',
            r'vbscript:',
            r'data:text/html',
        ]
        
        self.xss_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns]
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """Process incoming request untuk XSS protection."""
        # Check query parameters
        for key, value in request.query_params.items():
            if await self._contains_xss(value):
                if self.block_suspicious:
                    self.log_warning(f"XSS detected in query param {key}: {value}")
                    raise HTTPException(
                        status_code=400,
                        detail="Malicious content detected in request"
                    )
        
        return request
    
    async def process_response(self, request: Request, response: Response) -> Optional[Response]:
        """Process outgoing response untuk XSS protection headers."""
        # Add XSS protection headers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Add Content Security Policy
        csp = self.get_config('content_security_policy', 
                            "default-src 'self'; script-src 'self'")
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    async def validate_request(self, request: Request) -> bool:
        """Validate request untuk XSS threats."""
        # Check query parameters
        for value in request.query_params.values():
            if await self._contains_xss(value):
                return False
        
        return True
    
    async def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data untuk mencegah XSS."""
        if isinstance(data, str):
            return await self._sanitize_string(data)
        elif isinstance(data, dict):
            return {key: await self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [await self.sanitize_input(item) for item in data]
        else:
            return data
    
    async def _contains_xss(self, text: str) -> bool:
        """Check apakah text mengandung XSS patterns."""
        if not text:
            return False
        
        # Check against XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(text):
                return True
        
        return False
    
    async def _sanitize_string(self, text: str) -> str:
        """Sanitize string untuk mencegah XSS."""
        if not text:
            return text
        
        if self.auto_escape:
            # HTML escape
            text = html.escape(text)
        
        # Remove dangerous patterns
        for pattern in self.xss_patterns:
            text = pattern.sub('', text)
        
        return text

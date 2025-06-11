"""
Exception handling middleware implementation.
Mengimplementasikan centralized exception handling untuk aplikasi.
"""
from typing import Optional, Dict, Any, Type
import traceback
from datetime import datetime
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from middleware.core.abstract.base_middleware import BaseMiddleware


class CustomException(Exception):
    """Base class untuk custom exceptions."""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class ValidationException(CustomException):
    """Exception untuk validation errors."""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, status_code=400, error_code="VALIDATION_ERROR")


class AuthenticationException(CustomException):
    """Exception untuk authentication errors."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401, error_code="AUTHENTICATION_ERROR")


class AuthorizationException(CustomException):
    """Exception untuk authorization errors."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403, error_code="AUTHORIZATION_ERROR")


class NotFoundException(CustomException):
    """Exception untuk resource not found errors."""
    
    def __init__(self, message: str = "Resource not found", resource: str = None):
        self.resource = resource
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class BusinessLogicException(CustomException):
    """Exception untuk business logic errors."""
    
    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        super().__init__(message, status_code=422, error_code=error_code)


class ExceptionHandlerMiddleware(BaseMiddleware):
    """
    Exception Handler middleware untuk centralized exception handling.
    Menghandle semua exceptions dan mengembalikan response yang konsisten.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize exception handler middleware.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.debug_mode: bool = False
        self.log_exceptions: bool = True
        self.custom_handlers: Dict[Type[Exception], callable] = {}
    
    def setup(self) -> None:
        """Setup exception handler configuration."""
        self.debug_mode = self.get_config('debug_mode', False)
        self.log_exceptions = self.get_config('log_exceptions', True)
        
        # Setup custom exception handlers
        self._setup_custom_handlers()
    
    def _setup_custom_handlers(self) -> None:
        """Setup custom exception handlers."""
        self.custom_handlers = {
            HTTPException: self._handle_http_exception,
            CustomException: self._handle_custom_exception,
            ValidationException: self._handle_validation_exception,
            AuthenticationException: self._handle_authentication_exception,
            AuthorizationException: self._handle_authorization_exception,
            NotFoundException: self._handle_not_found_exception,
            BusinessLogicException: self._handle_business_logic_exception,
            ValueError: self._handle_value_error,
            KeyError: self._handle_key_error,
            AttributeError: self._handle_attribute_error,
            Exception: self._handle_generic_exception
        }
    
    async def process_request(self, request: Request) -> Optional[Request]:
        """
        Process request (tidak ada processing khusus untuk exception handler).
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Request object
        """
        return request
    
    async def handle_exception(self, request: Request, exc: Exception) -> Optional[Response]:
        """
        Handle exception yang terjadi dalam aplikasi.
        
        Args:
            request: FastAPI Request object
            exc: Exception yang terjadi
            
        Returns:
            JSON response untuk exception
        """
        try:
            # Log exception jika enabled
            if self.log_exceptions:
                await self._log_exception(request, exc)
            
            # Find appropriate handler
            handler = self._find_exception_handler(exc)
            
            # Handle exception
            if handler:
                return await handler(request, exc)
            
            # Fallback to generic handler
            return await self._handle_generic_exception(request, exc)
            
        except Exception as handler_exc:
            # Exception dalam exception handler - fallback ke basic response
            self.log_error(f"Exception in exception handler: {str(handler_exc)}", exc=handler_exc)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def _find_exception_handler(self, exc: Exception) -> Optional[callable]:
        """
        Find appropriate exception handler untuk exception type.
        
        Args:
            exc: Exception object
            
        Returns:
            Handler function atau None
        """
        # Check exact type match first
        exc_type = type(exc)
        if exc_type in self.custom_handlers:
            return self.custom_handlers[exc_type]
        
        # Check inheritance hierarchy
        for handler_type, handler in self.custom_handlers.items():
            if isinstance(exc, handler_type):
                return handler
        
        return None
    
    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> Response:
        """Handle FastAPI HTTPException."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    async def _handle_custom_exception(self, request: Request, exc: CustomException) -> Response:
        """Handle custom application exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    async def _handle_validation_exception(self, request: Request, exc: ValidationException) -> Response:
        """Handle validation exceptions."""
        content = {
            "error": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
        
        if exc.field:
            content["field"] = exc.field
        
        return JSONResponse(status_code=exc.status_code, content=content)
    
    async def _handle_authentication_exception(self, request: Request, exc: AuthenticationException) -> Response:
        """Handle authentication exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    async def _handle_authorization_exception(self, request: Request, exc: AuthorizationException) -> Response:
        """Handle authorization exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    async def _handle_not_found_exception(self, request: Request, exc: NotFoundException) -> Response:
        """Handle not found exceptions."""
        content = {
            "error": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
        
        if exc.resource:
            content["resource"] = exc.resource
        
        return JSONResponse(status_code=exc.status_code, content=content)
    
    async def _handle_business_logic_exception(self, request: Request, exc: BusinessLogicException) -> Response:
        """Handle business logic exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    async def _handle_value_error(self, request: Request, exc: ValueError) -> Response:
        """Handle ValueError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "VALUE_ERROR",
                "message": str(exc),
                "status_code": 400,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    async def _handle_key_error(self, request: Request, exc: KeyError) -> Response:
        """Handle KeyError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "error": "KEY_ERROR",
                "message": f"Missing required key: {str(exc)}",
                "status_code": 400,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    async def _handle_attribute_error(self, request: Request, exc: AttributeError) -> Response:
        """Handle AttributeError exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "ATTRIBUTE_ERROR",
                "message": "Internal server error - attribute not found",
                "status_code": 500,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    async def _handle_generic_exception(self, request: Request, exc: Exception) -> Response:
        """Handle generic exceptions."""
        content = {
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
        
        # Add exception details jika debug mode
        if self.debug_mode:
            content["exception_type"] = type(exc).__name__
            content["exception_message"] = str(exc)
            content["traceback"] = traceback.format_exc()
        
        return JSONResponse(status_code=500, content=content)
    
    async def _log_exception(self, request: Request, exc: Exception) -> None:
        """
        Log exception details.
        
        Args:
            request: FastAPI Request object
            exc: Exception object
        """
        try:
            log_data = {
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add user info jika tersedia
            if hasattr(request.state, 'user') and request.state.user:
                log_data["user_id"] = request.state.user.get('id', 'unknown')
            
            # Add request ID jika tersedia
            if hasattr(request.state, 'request_id'):
                log_data["request_id"] = request.state.request_id
            
            # Log dengan level yang sesuai
            if isinstance(exc, (CustomException, HTTPException)):
                if exc.status_code >= 500:
                    self.log_error(f"Server Error: {str(exc)}", exc=exc, **log_data)
                else:
                    self.log_warning(f"Client Error: {str(exc)}", **log_data)
            else:
                self.log_error(f"Unhandled Exception: {str(exc)}", exc=exc, **log_data)
                
        except Exception as log_exc:
            # Jangan biarkan logging error mengganggu exception handling
            print(f"Failed to log exception: {str(log_exc)}")

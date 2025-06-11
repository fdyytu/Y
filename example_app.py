"""
Example FastAPI application menggunakan middleware system.
Mendemonstrasikan penggunaan semua middleware yang telah diimplementasi.
"""
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import middleware components
from middleware import (
    initialize_middleware,
    get_middleware_stack,
    ExceptionHandlerMiddleware,
    CustomException,
    ValidationException,
    AuthenticationException,
    NotFoundException
)


class MiddlewareAdapter(BaseHTTPMiddleware):
    """
    Adapter untuk mengintegrasikan custom middleware dengan FastAPI.
    """
    
    def __init__(self, app, middleware_stack):
        super().__init__(app)
        self.middleware_stack = middleware_stack
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request melalui middleware stack.
        """
        try:
            # Process request melalui semua middleware
            for middleware in self.middleware_stack:
                if hasattr(middleware, 'process_request'):
                    result = await middleware.process_request(request)
                    if isinstance(result, JSONResponse):
                        # Middleware mengembalikan response langsung (e.g., cache hit, CORS preflight)
                        return result
            
            # Call next middleware/endpoint
            response = await call_next(request)
            
            # Process response melalui middleware (reverse order)
            for middleware in reversed(self.middleware_stack):
                if hasattr(middleware, 'process_response'):
                    result = await middleware.process_response(request, response)
                    if result:
                        response = result
            
            return response
            
        except Exception as exc:
            # Handle exceptions melalui exception handler
            exception_handler = None
            for middleware in self.middleware_stack:
                if isinstance(middleware, ExceptionHandlerMiddleware):
                    exception_handler = middleware
                    break
            
            if exception_handler:
                return await exception_handler.handle_exception(request, exc)
            
            # Fallback error response
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "message": str(exc)}
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting FastAPI application with middleware system...")
    
    # Initialize middleware system
    initialize_middleware()
    
    # Get middleware stack
    middleware_stack = get_middleware_stack()
    
    # Add middleware adapter to FastAPI
    app.add_middleware(MiddlewareAdapter, middleware_stack=middleware_stack)
    
    print(f"✅ Initialized {len(middleware_stack)} middleware components")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="Middleware System Demo",
    description="Demo aplikasi menggunakan custom middleware system",
    version="1.0.0",
    lifespan=lifespan
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Application is running"}


# Authentication endpoints
@app.post("/auth/login")
async def login(credentials: dict):
    """Login endpoint untuk mendapatkan JWT token."""
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        raise ValidationException("Username and password are required")
    
    # Simple authentication (dalam production, gunakan proper authentication)
    if username == "admin" and password == "password":
        from middleware.authentication.auth.jwt_middleware import JWTAuthStrategy
        
        jwt_strategy = JWTAuthStrategy(
            secret_key="your-jwt-secret-key",
            algorithm="HS256",
            expire_minutes=30
        )
        
        from uuid import UUID
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        token_data = await jwt_strategy.create_token(user_id)
        
        return {
            "access_token": token_data.access_token,
            "token_type": token_data.token_type,
            "expires_in": token_data.expires_in
        }
    
    raise AuthenticationException("Invalid credentials")


# Protected endpoint
@app.get("/protected")
async def protected_endpoint(request: Request):
    """Protected endpoint yang memerlukan authentication."""
    user = getattr(request.state, 'user', None)
    if not user:
        raise AuthenticationException("Authentication required")
    
    return {
        "message": "This is a protected endpoint",
        "user": user,
        "request_id": getattr(request.state, 'request_id', 'unknown')
    }


# API endpoints untuk testing
@app.get("/api/products")
async def get_products():
    """Get products (cacheable endpoint)."""
    # Simulate database query
    products = [
        {"id": 1, "name": "Product 1", "price": 100},
        {"id": 2, "name": "Product 2", "price": 200},
        {"id": 3, "name": "Product 3", "price": 300}
    ]
    return {"products": products}


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    """Get single product."""
    if product_id > 3:
        raise NotFoundException(f"Product with ID {product_id} not found", resource="product")
    
    return {
        "id": product_id,
        "name": f"Product {product_id}",
        "price": product_id * 100
    }


@app.post("/api/products")
async def create_product(product: dict, request: Request):
    """Create new product."""
    if not product.get("name"):
        raise ValidationException("Product name is required", field="name")
    
    if not product.get("price") or product["price"] <= 0:
        raise ValidationException("Product price must be greater than 0", field="price")
    
    # Simulate product creation
    new_product = {
        "id": 4,
        "name": product["name"],
        "price": product["price"]
    }
    
    return {"message": "Product created successfully", "product": new_product}


# Rate limiting test endpoint
@app.get("/api/test-rate-limit")
async def test_rate_limit():
    """Endpoint untuk testing rate limiting."""
    return {"message": "Rate limit test successful", "timestamp": "2024-01-01T00:00:00Z"}


# Error testing endpoints
@app.get("/api/test-error")
async def test_error():
    """Endpoint untuk testing error handling."""
    raise CustomException("This is a test error", status_code=400, error_code="TEST_ERROR")


@app.get("/api/test-server-error")
async def test_server_error():
    """Endpoint untuk testing server error."""
    raise Exception("This is a test server error")


# CORS test endpoint
@app.options("/api/cors-test")
async def cors_preflight():
    """CORS preflight akan dihandle oleh CORS middleware."""
    return {"message": "This should not be reached"}


@app.get("/api/cors-test")
async def cors_test():
    """CORS test endpoint."""
    return {"message": "CORS test successful"}


if __name__ == "__main__":
    print("🌟 Starting Middleware Demo Application...")
    print("📚 Available endpoints:")
    print("  - GET  /health                 - Health check")
    print("  - POST /auth/login             - Login (username: admin, password: password)")
    print("  - GET  /protected              - Protected endpoint (requires JWT)")
    print("  - GET  /api/products           - Get products (cached)")
    print("  - GET  /api/products/{id}      - Get single product")
    print("  - POST /api/products           - Create product")
    print("  - GET  /api/test-rate-limit    - Test rate limiting")
    print("  - GET  /api/test-error         - Test error handling")
    print("  - GET  /api/test-server-error  - Test server error")
    print("  - GET  /api/cors-test          - Test CORS")
    print("\n🔧 Middleware features:")
    print("  - JWT Authentication")
    print("  - CORS handling")
    print("  - Rate limiting (Token bucket)")
    print("  - Response caching")
    print("  - Request/Response logging")
    print("  - Exception handling")
    print("\n🚀 Starting server on http://0.0.0.0:8000")
    
    uvicorn.run(
        "example_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

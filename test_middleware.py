"""
Test script untuk middleware system.
Testing semua komponen middleware secara unit test.
"""
import asyncio
import sys
import os

# Add middleware to path
sys.path.insert(0, '/home/user/workspace')

from middleware import (
    initialize_middleware,
    get_middleware_stack,
    JWTMiddleware,
    CORSMiddleware,
    RateLimitMiddleware,
    CacheMiddleware,
    RequestLoggerMiddleware,
    ExceptionHandlerMiddleware
)


async def test_middleware_initialization():
    """Test middleware initialization."""
    print("🧪 Testing middleware initialization...")
    
    try:
        # Initialize middleware
        initialize_middleware()
        print("✅ Middleware initialization successful")
        
        # Get middleware stack
        middleware_stack = get_middleware_stack()
        print(f"✅ Got middleware stack with {len(middleware_stack)} components")
        
        # Print middleware details
        for i, middleware in enumerate(middleware_stack):
            print(f"  {i+1}. {middleware.__class__.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Middleware initialization failed: {str(e)}")
        return False


async def test_jwt_middleware():
    """Test JWT middleware."""
    print("\n🧪 Testing JWT middleware...")
    
    try:
        from middleware.authentication.auth.jwt_middleware import JWTAuthStrategy
        from uuid import UUID
        
        # Create JWT strategy
        jwt_strategy = JWTAuthStrategy(
            secret_key="test-secret-key",
            algorithm="HS256",
            expire_minutes=30
        )
        
        # Test token creation
        user_id = UUID('12345678-1234-5678-1234-567812345678')
        token_data = await jwt_strategy.create_token(user_id)
        print(f"✅ JWT token created: {token_data.access_token[:20]}...")
        
        # Test token validation
        user_data = await jwt_strategy.validate_token(token_data.access_token)
        print(f"✅ JWT token validated: {user_data}")
        
        return True
        
    except Exception as e:
        print(f"❌ JWT middleware test failed: {str(e)}")
        return False


async def test_rate_limiter():
    """Test rate limiter."""
    print("\n🧪 Testing rate limiter...")
    
    try:
        from middleware.performance.rate_limiter import TokenBucketRateLimiter
        
        # Create rate limiter
        limiter = TokenBucketRateLimiter(capacity=5, refill_rate=1.0)
        
        # Test token consumption
        for i in range(3):
            allowed = await limiter.consume()
            print(f"  Request {i+1}: {'✅ Allowed' if allowed else '❌ Denied'}")
        
        # Check remaining tokens
        remaining = await limiter.get_remaining_tokens()
        print(f"✅ Remaining tokens: {remaining}")
        
        return True
        
    except Exception as e:
        print(f"❌ Rate limiter test failed: {str(e)}")
        return False


async def test_cache():
    """Test cache middleware."""
    print("\n🧪 Testing cache...")
    
    try:
        from middleware.performance.cache_middleware import InMemoryCache
        
        # Create cache
        cache = InMemoryCache()
        
        # Test cache operations
        await cache.set("test_key", {"data": "test_value"}, ttl=60)
        print("✅ Cache set successful")
        
        value = await cache.get("test_key")
        print(f"✅ Cache get successful: {value}")
        
        deleted = await cache.delete("test_key")
        print(f"✅ Cache delete successful: {deleted}")
        
        # Test expired key
        value_after_delete = await cache.get("test_key")
        print(f"✅ Cache get after delete: {value_after_delete}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {str(e)}")
        return False


async def test_exception_handler():
    """Test exception handler."""
    print("\n🧪 Testing exception handler...")
    
    try:
        from middleware.error.exception_handler import (
            CustomException,
            ValidationException,
            AuthenticationException,
            NotFoundException
        )
        
        # Test custom exceptions
        exceptions = [
            CustomException("Test error", status_code=400),
            ValidationException("Invalid field", field="test_field"),
            AuthenticationException("Auth required"),
            NotFoundException("Resource not found", resource="test")
        ]
        
        for exc in exceptions:
            print(f"✅ Exception created: {exc.__class__.__name__} - {exc.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Exception handler test failed: {str(e)}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting middleware system tests...")
    print("=" * 50)
    
    tests = [
        test_middleware_initialization,
        test_jwt_middleware,
        test_rate_limiter,
        test_cache,
        test_exception_handler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Middleware system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())

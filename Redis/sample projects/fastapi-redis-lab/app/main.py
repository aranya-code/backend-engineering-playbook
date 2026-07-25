"""FastAPI Redis Lab - Main application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.redis_client import close_redis
from app.routers import products, cart, auth, analytics, redis_examples


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    print("=" * 50)
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print("=" * 50)
    
    # Initialize database
    print("Initializing database...")
    await init_db()
    print("✓ Database initialized")
    
    # Test Redis connection
    print("Testing Redis connection...")
    from app.redis_client import get_redis
    try:
        redis = await get_redis()
        await redis.ping()
        print("✓ Redis connected")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}")
        print("  Make sure Redis is running on localhost:6379")
    
    print("=" * 50)
    print("Application started successfully!")
    print(f"API Documentation: http://localhost:8000/docs")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print("\nShutting down...")
    await close_redis()
    await close_db()
    print("✓ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    FastAPI Redis Lab - A comprehensive demonstration of Redis integration with FastAPI.
    
    ## Features
    
    * **Product Catalog** - CRUD operations with Redis caching
    * **Shopping Cart** - Redis Hash for cart management
    * **Authentication** - OTP-based login with Redis TTL
    * **Rate Limiting** - Request throttling using Redis
    * **Analytics** - HyperLogLog, Bitmaps, and Sorted Sets
    * **Pub/Sub** - Real-time messaging
    * **Streams** - Event sourcing and message queues
    * **Distributed Locks** - Prevent race conditions
    * **Background Tasks** - Celery with Redis broker
    
    ## Redis Data Structures Used
    
    * Strings (caching, counters)
    * Hashes (shopping cart)
    * Sets
    * Sorted Sets (leaderboards)
    * HyperLogLog (unique visitors)
    * Bitmaps (daily active users)
    * Streams (event sourcing)
    * Pub/Sub (real-time messaging)
    """,
    lifespan=lifespan,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(auth.router)
app.include_router(analytics.router)
app.include_router(redis_examples.router)


# Root endpoint

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "FastAPI Redis Lab - Redis integration examples",
        "documentation": "/docs",
        "health": "/redis/health",
        "features": [
            "Product caching",
            "Shopping cart (Redis Hash)",
            "OTP authentication",
            "Rate limiting",
            "View counters",
            "Leaderboards (Sorted Sets)",
            "Pub/Sub messaging",
            "Redis Streams",
            "Distributed locks",
            "Celery background tasks",
            "HyperLogLog (unique visitors)",
            "Bitmaps (daily active users)"
        ]
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """
    Application health check.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

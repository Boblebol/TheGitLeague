"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router
from app.middleware.security import SecurityHeadersMiddleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Transform your Git activity into an NBA-style league",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS (restricted for security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Restricted from wildcard
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
    ],  # Restricted from wildcard
    expose_headers=["Content-Range", "X-Total-Count"],
)

# Add rate limiting
if settings.ENABLE_RATE_LIMITING:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": settings.VERSION,
        },
    )


@app.get("/api/v1")
async def api_root():
    """API v1 root endpoint."""
    return {
        "message": "The Git League API v1",
        "version": settings.VERSION,
        "docs": "/docs",
    }


# Event handlers
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print(f"🏀 Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 API Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print(f"👋 Shutting down {settings.APP_NAME}")

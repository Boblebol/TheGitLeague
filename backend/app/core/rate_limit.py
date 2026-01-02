"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.

    Checks X-Forwarded-For header first (for proxies/load balancers),
    then falls back to direct connection IP.
    """
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can be a comma-separated list, take the first one
        return forwarded.split(",")[0].strip()

    # Fallback to direct connection
    return get_remote_address(request)


# Initialize rate limiter
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    enabled=settings.ENABLE_RATE_LIMITING,
    storage_uri="memory://",  # Use Redis in production: redis://localhost:6379
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Returns:
        JSONResponse with 429 status code and retry-after header
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Please try again in {exc.detail}.",
        },
        headers={
            "Retry-After": str(exc.detail.split()[-1]),  # Extract seconds from detail
        },
    )

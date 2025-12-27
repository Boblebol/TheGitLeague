"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import auth, users

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(users.router)

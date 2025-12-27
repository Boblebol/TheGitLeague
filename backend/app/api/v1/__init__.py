"""API v1 routes."""

from fastapi import APIRouter

from app.api.v1 import auth, users, projects, repos, commits, scoring, seasons

api_router = APIRouter()

# Include routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(repos.router)
api_router.include_router(commits.router)
api_router.include_router(scoring.router)
api_router.include_router(seasons.router)

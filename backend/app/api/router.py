from fastapi import APIRouter
from app.api.endpoints import analytics, posts, scraper

api_router = APIRouter()

api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.router import api_router
from app.services.scraper_service import scraper_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("karhutla_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")

        # Seed initial dataset if empty so dashboard is immediately informative
        from sqlalchemy import select, func
        from app.core.database import AsyncSessionLocal
        from app.models.post import Post

        async with AsyncSessionLocal() as session:
            res = await session.execute(select(func.count(Post.id)))
            count = res.scalar() or 0
            if count == 0:
                logger.info("Database empty on startup. Triggering initial data seed...")
                await scraper_service.run_scrape_pipeline(
                    keyword="karhutla",
                    method="playwright",
                    max_posts=12
                )
    except Exception as e:
        logger.error(f"Error during application startup: {e}")

    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "database": "postgresql://localhost:5433/threads_karhutla",
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "message": f"{settings.PROJECT_NAME} API is running",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }

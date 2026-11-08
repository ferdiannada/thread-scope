from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ThreadScope - Sentiment Intelligence"
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/threads_karhutla"
    
    # Sentiment Engine Configuration ("indobert", "gemini", or "hybrid")
    SENTIMENT_ENGINE: str = "indobert"
    INDOBERT_MODEL_NAME: str = "ayameRushia/bert-base-indonesian-1.5G-sentiment-analysis-smsa"
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Meta Threads Official API credentials (Optional)
    THREADS_APP_ID: str = ""
    THREADS_APP_SECRET: str = ""
    THREADS_ACCESS_TOKEN: str = ""
    THREADS_SESSION_ID: str = ""
    
    # Scraper settings (Opini, keluhan publik, dan percakapan warga Threads)
    DEFAULT_KEYWORDS: List[str] = [
        "karhutla",
        "timnas indonesia",
        "kecerdasan buatan",
        "kebijakan publik",
        "kuliner indonesia",
        "cuaca ekstrem",
    ]
    PLAYWRIGHT_HEADLESS: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

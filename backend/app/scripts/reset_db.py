import asyncio
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models.post import Post
from app.models.sentiment import Sentiment
from app.models.scraper_log import ScraperLog


async def reset():
    print("Clearing database to start fresh...")
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Sentiment))
        await session.execute(delete(Post))
        await session.execute(delete(ScraperLog))
        await session.commit()
    print("Database cleared successfully. Ready for fresh scraping!")


if __name__ == "__main__":
    asyncio.run(reset())

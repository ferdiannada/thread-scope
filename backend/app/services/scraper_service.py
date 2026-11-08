import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.post import Post
from app.models.sentiment import Sentiment
from app.models.scraper_log import ScraperLog
from app.schemas.post import PostCreate
from app.scraper.playwright_scraper import PlaywrightThreadsScraper
from app.scraper.official_api import OfficialThreadsClient
from app.services.sentiment_service import sentiment_service

logger = logging.getLogger(__name__)


class ScraperService:
    async def run_scrape_pipeline(
        self,
        keyword: str,
        method: str = "playwright",
        max_posts: int = 25,
        log_id: Optional[UUID] = None,
        clear_existing: bool = False,
    ):
        """
        Executes end-to-end scraping and sentiment analysis pipeline in background.
        """
        async with AsyncSessionLocal() as session:
            # If clear_existing requested directly on pipeline
            if clear_existing:
                from sqlalchemy import delete
                await session.execute(delete(Sentiment))
                await session.execute(delete(Post))
                await session.commit()

            # Create or update log entry
            log_entry = None
            if log_id:
                log_entry = await session.get(ScraperLog, log_id)
                if log_entry:
                    log_entry.status = "running"
                    log_entry.started_at = datetime.now(timezone.utc)
                    log_entry.error_message = "Menyiapkan engine scraping & inisialisasi browser..."
                    await session.commit()
            if not log_entry:
                log_entry = ScraperLog(
                    keyword=keyword,
                    method=method,
                    status="running",
                    started_at=datetime.now(timezone.utc),
                    error_message="Menyiapkan engine scraping & inisialisasi browser...",
                )
                session.add(log_entry)
                await session.commit()
                await session.refresh(log_entry)

            try:
                # Select scraper engine
                if method == "official_api":
                    scraper = OfficialThreadsClient()
                else:
                    scraper = PlaywrightThreadsScraper()

                # Step 1: Scrape posts
                log_entry.error_message = f"Mengambil data Threads untuk '{keyword}' (target: {max_posts} post)..."
                await session.commit()

                raw_posts: List[PostCreate] = await scraper.search_posts(
                    keyword=keyword, limit=max_posts
                )
                log_entry.posts_found = len(raw_posts)
                log_entry.error_message = f"Ditemukan {len(raw_posts)} post. Memeriksa duplikasi database..."
                await session.commit()

                if not raw_posts:
                    log_entry.status = "success"
                    log_entry.posts_inserted = 0
                    log_entry.error_message = "Tidak ada postingan baru ditemukan dari kueri pencarian."
                    log_entry.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    return

                # Step 2: Deduplicate against existing posts and contents in database
                post_ids = [p.id for p in raw_posts]
                existing_ids_res = await session.execute(select(Post.id).where(Post.id.in_(post_ids)))
                existing_ids = set(existing_ids_res.scalars().all())

                clean_contents = [p.content.strip() for p in raw_posts if p.content]
                existing_contents = set()
                if clean_contents:
                    existing_contents_res = await session.execute(
                        select(Post.content).where(Post.content.in_(clean_contents))
                    )
                    existing_contents = set(existing_contents_res.scalars().all())

                seen_batch_ids = set()
                seen_batch_contents = set()
                new_posts = []

                for p in raw_posts:
                    c_clean = p.content.strip()
                    if p.id in existing_ids or p.id in seen_batch_ids:
                        continue
                    if c_clean in existing_contents or c_clean in seen_batch_contents:
                        continue

                    seen_batch_ids.add(p.id)
                    seen_batch_contents.add(c_clean)
                    new_posts.append(p)

                duplicates_count = len(raw_posts) - len(new_posts)

                if not new_posts:
                    msg = f"Semua {len(raw_posts)} post yang ditemukan sudah tersimpan sebelumnya di database."
                    logger.info(msg)
                    log_entry.status = "success"
                    log_entry.posts_inserted = 0
                    log_entry.error_message = msg
                    log_entry.completed_at = datetime.now(timezone.utc)
                    await session.commit()
                    return

                # Step 3: Sentiment & Entity Analysis via Gemini Flash (or fallback)
                log_entry.error_message = f"Menganalisis sentimen AI untuk {len(new_posts)} post baru..."
                await session.commit()

                logger.info(
                    f"Running sentiment analysis for {len(new_posts)} new posts ({duplicates_count} duplikat dilewati)..."
                )
                sentiment_map = await sentiment_service.analyze_posts(new_posts)

                # Step 4: Persist Posts and Sentiments
                log_entry.error_message = f"Menyimpan {len(new_posts)} post & sentimen ke database..."
                await session.commit()
                inserted_count = 0
                for p_create in new_posts:
                    db_post = Post(
                        id=p_create.id,
                        author_username=p_create.author_username,
                        author_name=p_create.author_name,
                        author_profile_pic=p_create.author_profile_pic,
                        content=p_create.content,
                        post_url=p_create.post_url,
                        likes_count=p_create.likes_count,
                        replies_count=p_create.replies_count,
                        reposts_count=p_create.reposts_count,
                        posted_at=p_create.posted_at,
                        media_urls=p_create.media_urls,
                        raw_metadata=p_create.raw_metadata,
                    )
                    session.add(db_post)

                    # Add sentiment if extracted
                    analysis = sentiment_map.get(p_create.id)
                    if analysis:
                        db_sentiment = Sentiment(
                            post_id=p_create.id,
                            sentiment_label=analysis.sentiment,
                            confidence_score=analysis.confidence,
                            primary_emotion=analysis.emotion,
                            summary_reason=analysis.summary_reason,
                            locations=analysis.locations,
                            entities=analysis.entities,
                        )
                        session.add(db_sentiment)

                    inserted_count += 1

                log_entry.posts_inserted = inserted_count
                log_entry.status = "success"
                if duplicates_count > 0:
                    log_entry.error_message = f"Berhasil menyimpan {inserted_count} postingan baru ({duplicates_count} postingan lama dilewati)."
                log_entry.completed_at = datetime.now(timezone.utc)
                await session.commit()
                logger.info(
                    f"Scraping & sentiment pipeline completed successfully. Inserted {inserted_count} posts."
                )

            except Exception as e:
                logger.error(f"Error in scraping pipeline for '{keyword}': {e}", exc_info=True)
                log_entry.status = "failed"
                log_entry.error_message = str(e)
                log_entry.completed_at = datetime.now(timezone.utc)
                await session.commit()


scraper_service = ScraperService()

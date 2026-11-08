import uuid
from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.scraper_log import ScraperLog
from app.schemas.scraper import (
    ScraperTriggerRequest,
    ScraperTriggerResponse,
    ScraperLogResponse,
)
from app.services.scraper_service import scraper_service

router = APIRouter()


@router.post("/trigger", response_model=ScraperTriggerResponse)
async def trigger_scraper(
    payload: ScraperTriggerRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually triggers a Threads scraping & sentiment analysis pipeline in the background.
    """
    keywords = payload.keywords or settings.DEFAULT_KEYWORDS[:3]
    task_id = str(uuid.uuid4())

    if payload.clear_existing:
        from sqlalchemy import delete
        from app.models.post import Post
        from app.models.sentiment import Sentiment
        await db.execute(delete(Sentiment))
        await db.execute(delete(Post))
        await db.commit()

    for kw in keywords:
        log_id = uuid.uuid4()
        new_log = ScraperLog(
            id=log_id,
            keyword=kw,
            method=payload.method,
            status="queued",
            error_message="Menunggu giliran eksekusi di latar belakang..." if not payload.clear_existing else "Data lama telah dibersihkan. Menunggu eksekusi scraping baru...",
        )
        db.add(new_log)
        await db.commit()

        background_tasks.add_task(
            scraper_service.run_scrape_pipeline,
            keyword=kw,
            method=payload.method,
            max_posts=payload.max_posts,
            log_id=log_id,
            clear_existing=False,
        )

    msg = f"Job scraping berhasil dipicu untuk {len(keywords)} kata kunci."
    if payload.clear_existing:
        msg = f"Data lama berhasil dibersihkan (timpa). Job scraping baru dipicu untuk {len(keywords)} kata kunci."

    return ScraperTriggerResponse(
        message=msg,
        task_id=task_id,
        keywords=keywords,
        method=payload.method,
        clear_existing=payload.clear_existing,
    )


@router.get("/status", response_model=List[ScraperLogResponse])
async def get_scraper_logs(
    limit: int = 15,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns latest scraper execution logs and statuses.
    Auto-cleans stale jobs that have been stuck in 'running' or 'queued' for > 5 minutes.
    """
    now = datetime.now(timezone.utc)
    stale_cutoff = now - timedelta(minutes=5)

    stale_query = select(ScraperLog).where(
        ScraperLog.status.in_(["running", "queued"]),
        ScraperLog.started_at < stale_cutoff,
    )
    stale_res = await db.execute(stale_query)
    stale_logs = stale_res.scalars().all()
    if stale_logs:
        for s_log in stale_logs:
            s_log.status = "failed"
            s_log.error_message = "Timeout: Pekerjaan scraping melebihi batas waktu maksimal (5 menit)."
            s_log.completed_at = now
        await db.commit()

    query = select(ScraperLog).order_by(desc(ScraperLog.started_at)).limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()
    return [ScraperLogResponse.model_validate(l) for l in logs]


@router.post("/reset-stuck")
async def reset_stuck_jobs(db: AsyncSession = Depends(get_db)):
    """
    Resets any stuck running or queued scraper jobs so UI can immediately resume.
    """
    now = datetime.now(timezone.utc)
    query = select(ScraperLog).where(ScraperLog.status.in_(["running", "queued"]))
    res = await db.execute(query)
    stuck = res.scalars().all()
    for item in stuck:
        item.status = "failed"
        item.error_message = "Dibatalkan secara manual oleh pengguna."
        item.completed_at = now
    if stuck:
        await db.commit()
    return {"message": f"Berhasil mereset {len(stuck)} pekerjaan scraper yang tertahan."}


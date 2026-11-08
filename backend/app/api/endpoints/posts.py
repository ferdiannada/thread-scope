import math
from typing import Optional
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.post import Post
from app.models.sentiment import Sentiment
from app.schemas.post import PaginatedPostsResponse, PostResponse

router = APIRouter()

ALLOWED_IMAGE_HOSTS = {
    "fbcdn.net",
    "cdninstagram.com",
    "threads.net",
    "instagram.com",
}


@router.get("/proxy-image")
async def proxy_image(url: str = Query(..., description="External image URL to proxy")):
    """
    Proxy image endpoint to circumvent Cross-Origin-Resource-Policy (CORP) blocks
    from Meta/Instagram CDNs (fbcdn.net).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise HTTPException(status_code=400, detail="Invalid URL scheme")

        hostname = (parsed.hostname or "").lower()
        if not any(hostname == allowed or hostname.endswith("." + allowed) for allowed in ALLOWED_IMAGE_HOSTS):
            raise HTTPException(status_code=403, detail="Host not permitted for image proxy")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail="Malformed URL")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://www.threads.net/",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="Remote server returned error")

            content_type = resp.headers.get("content-type", "image/jpeg")
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Cross-Origin-Resource-Policy": "cross-origin",
                    "Access-Control-Allow-Origin": "*",
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch image: {str(e)}")


@router.get("", response_model=PaginatedPostsResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sentiment: Optional[str] = Query(None, description="positive, neutral, negative"),
    keyword: Optional[str] = Query(None, description="Search term in content or author"),
    emotion: Optional[str] = Query(None, description="anger, anxiety, sadness, hope, neutral"),
    location: Optional[str] = Query(None, description="Specific location mentioned"),
    db: AsyncSession = Depends(get_db),
):
    """
    List posts with multi-dimensional filtering and pagination.
    """
    query = select(Post).options(selectinload(Post.sentiment))
    count_query = select(func.count(Post.id))

    if sentiment or emotion or location:
        query = query.join(Sentiment, Post.id == Sentiment.post_id)
        count_query = count_query.join(Sentiment, Post.id == Sentiment.post_id)

        if sentiment:
            query = query.where(Sentiment.sentiment_label == sentiment)
            count_query = count_query.where(Sentiment.sentiment_label == sentiment)

        if emotion:
            query = query.where(Sentiment.primary_emotion == emotion)
            count_query = count_query.where(Sentiment.primary_emotion == emotion)

        if location:
            # Check JSONB array containing location
            query = query.where(Sentiment.locations.contains([location]))
            count_query = count_query.where(Sentiment.locations.contains([location]))

    if keyword:
        search_filter = Post.content.ilike(f"%{keyword}%") | Post.author_username.ilike(f"%{keyword}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Order by newest
    query = query.order_by(desc(Post.posted_at))

    # Pagination
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)
    res = await db.execute(paginated_query)
    items = res.scalars().all()

    total_pages = math.ceil(total / limit) if total > 0 else 1

    return PaginatedPostsResponse(
        items=[PostResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )

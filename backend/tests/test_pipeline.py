import pytest
from app.schemas.post import PostCreate
from app.services.sentiment_service import sentiment_service


@pytest.mark.asyncio
async def test_heuristic_sentiment_analysis():
    # Test Negative
    sample_negative = PostCreate(
        id="test_neg_1",
        author_username="user_riau",
        content="Asap karhutla di Pekanbaru makin pekat dan dada sesak, mata perih banget!",
        likes_count=10,
        replies_count=2,
        reposts_count=1,
        posted_at="2026-11-06T10:00:00Z",
    )
    res_neg = sentiment_service._analyze_single_heuristic(sample_negative)
    assert res_neg.sentiment == "negative"
    assert "Riau" in res_neg.locations or "Pekanbaru" in res_neg.locations

    # Test Positive
    sample_positive = PostCreate(
        id="test_pos_1",
        author_username="user_kalteng",
        content="Alhamdulillah Palangkaraya sore ini diguyur hujan deras, titik api padam!",
        likes_count=50,
        replies_count=5,
        reposts_count=12,
        posted_at="2026-11-06T10:00:00Z",
    )
    res_pos = sentiment_service._analyze_single_heuristic(sample_positive)
    assert res_pos.sentiment == "positive"
    assert res_pos.emotion == "hope"
    assert "Palangkaraya" in res_pos.locations

    # Test Neutral
    sample_neutral = PostCreate(
        id="test_neu_1",
        author_username="bmkg_update",
        content="Laporan BMKG: Terpantau 24 titik panas di wilayah Kalimantan Barat.",
        likes_count=20,
        replies_count=0,
        reposts_count=4,
        posted_at="2026-11-06T10:00:00Z",
    )
    res_neu = sentiment_service._analyze_single_heuristic(sample_neutral)
    assert res_neu.sentiment == "neutral"
    assert "BMKG" in res_neu.entities


@pytest.mark.asyncio
async def test_proxy_image_validation():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Non-permitted host should return 403 Forbidden
        res_forbidden = await client.get("/api/v1/posts/proxy-image?url=https://attacker.com/leak.png")
        assert res_forbidden.status_code == 403

        # Invalid URL scheme should return 400 Bad Request
        res_invalid = await client.get("/api/v1/posts/proxy-image?url=ftp://fbcdn.net/test.jpg")
        assert res_invalid.status_code == 400


@pytest.mark.asyncio
async def test_scraper_status_and_reset():
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Check status endpoint
        res_status = await client.get("/api/v1/scraper/status")
        assert res_status.status_code == 200
        assert isinstance(res_status.json(), list)

        # Check reset endpoint
        res_reset = await client.post("/api/v1/scraper/reset-stuck")
        assert res_reset.status_code == 200
        assert "Berhasil" in res_reset.json()["message"]


@pytest.mark.asyncio
async def test_scraper_trigger_schema_clear_existing():
    from app.schemas.scraper import ScraperTriggerRequest

    # Default is False (accumulate / jangan hapus data lama)
    req_default = ScraperTriggerRequest(keywords=["karhutla"])
    assert req_default.clear_existing is False

    # Option to wipe & replace (timpa)
    req_wipe = ScraperTriggerRequest(keywords=["karhutla"], clear_existing=True)
    assert req_wipe.clear_existing is True


def test_dynamic_posts_uniqueness():
    from app.scraper.playwright_scraper import PlaywrightThreadsScraper

    scraper = PlaywrightThreadsScraper()
    for limit in [25, 50, 75]:
        posts = scraper._generate_dynamic_posts("Sidang Jokowi", limit)
        assert len(posts) == limit
        unique_ids = {p.id for p in posts}
        unique_contents = {p.content.strip() for p in posts}
        assert len(unique_ids) == limit, f"Expected {limit} unique IDs, got {len(unique_ids)}"
        assert len(unique_contents) == limit, f"Expected {limit} unique contents, got {len(unique_contents)}"

import pytest
from app.services.normalizer import TextNormalizer
from app.schemas.post import PostCreate


def test_text_normalizer_slang_and_codemixing():
    raw_text = "Gilaaa parah bgt kabut asap hari ini woyyy, gw ga bisa napas! Plis help @jokowi https://threads.net"
    cleaned = TextNormalizer.clean_text(raw_text)

    # Verifikasi pembersihan URL dan mention
    assert "https://threads.net" not in cleaned
    assert "@jokowi" not in cleaned

    # Verifikasi normalisasi karakter berulang
    assert "gilaaa" not in cleaned
    assert "woyyy" not in cleaned

    # Verifikasi kamus slang Indonesia
    assert "parah sekali" in cleaned
    assert "tidak" in cleaned
    assert "saya" in cleaned
    assert "tolong" in cleaned


def test_text_normalizer_appreciation():
    raw_text = "Alhamdulillah hujan deres bgt di Pekanbaru, asap mulai hilang. Stay safe semuanya!"
    cleaned = TextNormalizer.clean_text(raw_text)

    assert "alhamdulillah bersyukur" in cleaned
    assert "banget" in cleaned
    assert "tetap aman" in cleaned


def test_indobert_sentiment_and_sarcasm():
    from app.services.indobert_service import indobert_service
    from datetime import datetime

    test_posts = [
        PostCreate(
            id="test-1",
            author_username="warga_riau",
            content="Alhamdulillah hujan deras banget di Pekanbaru, kabut asap akhirnya mulai berkurang drastis",
            posted_at=datetime.now(),
        ),
        PostCreate(
            id="test-2",
            author_username="korban_asap",
            content="gila parah bgt kabut asap hari ini, sesak napas woy ga bisa keluar rumah",
            posted_at=datetime.now(),
        ),
        PostCreate(
            id="test-3",
            author_username="sarkas_user",
            content="Keren bgt pemda santai bgt padahal asap udah tebal pekat gini, mantap lah",
            posted_at=datetime.now(),
        ),
        PostCreate(
            id="test-4",
            author_username="bmkg_update",
            content="BMKG merilis pantauan satelit ada 15 titik panas terpantau di Kalimantan Tengah",
            posted_at=datetime.now(),
        ),
    ]

    results = indobert_service.analyze_posts_batch(test_posts)

    assert results["test-1"].sentiment == "positive"
    assert results["test-1"].emotion == "hope"
    assert "Pekanbaru" in results["test-1"].locations

    assert results["test-2"].sentiment == "negative"
    assert results["test-2"].emotion in ["anger", "anxiety"]

    # Sarkasme harus terdeteksi sebagai negative dengan emosi anger
    assert results["test-3"].sentiment == "negative"
    assert results["test-3"].emotion == "anger"

    assert results["test-4"].sentiment == "neutral"


def test_dynamic_topic_sentiment_and_locations():
    from app.services.indobert_service import indobert_service
    from datetime import datetime

    dynamic_posts = [
        PostCreate(
            id="dyn-1",
            author_username="tech_enthusiast",
            content="Keren banget perkembangan Kecerdasan Buatan di Jakarta, makin banyak inovasi bermanfaat! #AI",
            posted_at=datetime.now(),
            raw_metadata={"keyword": "Kecerdasan Buatan"},
        ),
        PostCreate(
            id="dyn-2",
            author_username="suporter_bola",
            content="Kecewa banget sama performa Timnas Indonesia semalam di Surabaya, mainnya lambat dan banyak blunder",
            posted_at=datetime.now(),
            raw_metadata={"keyword": "Timnas Indonesia"},
        ),
    ]

    results = indobert_service.analyze_posts_batch(dynamic_posts)

    assert results["dyn-1"].sentiment == "positive"
    assert "Jakarta" in results["dyn-1"].locations
    assert "Kecerdasan Buatan" in results["dyn-1"].entities or "#AI" in results["dyn-1"].entities
    assert "Kecerdasan Buatan" in results["dyn-1"].summary_reason

    assert results["dyn-2"].sentiment == "negative"
    assert "Surabaya" in results["dyn-2"].locations
    assert "Timnas Indonesia" in results["dyn-2"].entities
    assert "Timnas Indonesia" in results["dyn-2"].summary_reason


def test_indobert_advanced_slang_emoji_and_sarcasm():
    from app.services.indobert_service import indobert_service
    from datetime import datetime

    test_nuanced_posts = [
        # 1. Slang positif modern (gacor, mantul, no debat)
        PostCreate(
            id="slang-pos",
            author_username="user_hype",
            content="Performa aplikasinya gacor mantul parah, fix no debat juara! 🔥✨",
            posted_at=datetime.now(),
        ),
        # 2. Sarkasme lintas topik non-karhutla (pelayanan lambat dengan pujian semu dan emoji badut)
        PostCreate(
            id="sarcasm-service",
            author_username="warga_sarkas",
            content="Keren banget ya pelayanannya, antre 5 jam baru dipanggil, mantap betul 🤡",
            posted_at=datetime.now(),
        ),
        # 3. Negasi kompleks (jauh dari kata memuaskan)
        PostCreate(
            id="negation-complex",
            author_username="reviewer_jujur",
            content="Pelayanannya tidak ramah dan jauh dari kata memuaskan, sangat mengecewakan",
            posted_at=datetime.now(),
        ),
        # 4. Emoji dan emosi kesedihan mendalam
        PostCreate(
            id="emoji-sadness",
            author_username="citizen_sympathy",
            content="Sedih banget liat korbannya, nyesek di dada liat beritanya 😭💔",
            posted_at=datetime.now(),
        ),
    ]

    results = indobert_service.analyze_posts_batch(test_nuanced_posts)

    # 1. Slang positif harus positive dengan emosi hope
    assert results["slang-pos"].sentiment == "positive"
    assert results["slang-pos"].emotion == "hope"

    # 2. Sarkasme non-karhutla harus terdeteksi negative dengan emosi anger
    assert results["sarcasm-service"].sentiment == "negative"
    assert results["sarcasm-service"].emotion == "anger"

    # 3. Negasi kompleks harus negative
    assert results["negation-complex"].sentiment == "negative"

    # 4. Kesedihan dan emoji sedih harus negative dengan emosi sadness
    assert results["emoji-sadness"].sentiment == "negative"
    assert results["emoji-sadness"].emotion == "sadness"

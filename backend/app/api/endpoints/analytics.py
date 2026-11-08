from datetime import datetime, timezone, timedelta
from typing import List, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.post import Post
from app.models.sentiment import Sentiment
from app.schemas.analytics import (
    OverviewMetrics,
    SentimentSummary,
    EmotionSummary,
    EntityMetric,
    RegionalFactReport,
    TimelinePoint,
)

router = APIRouter()


@router.get("/overview", response_model=OverviewMetrics)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated KPIs: total posts, sentiment distribution, emotions,
    factual regional intelligence reports, and top entities.
    """
    # Total posts
    total_posts_res = await db.execute(select(func.count(Post.id)))
    total_posts = total_posts_res.scalar() or 0

    # Engagement
    engagement_res = await db.execute(
        select(
            func.coalesce(func.sum(Post.likes_count), 0),
            func.coalesce(func.sum(Post.replies_count), 0),
        )
    )
    total_likes, total_replies = engagement_res.one()

    # Sentiment distribution
    sentiment_query = select(
        Sentiment.sentiment_label, func.count(Sentiment.id)
    ).group_by(Sentiment.sentiment_label)
    sentiment_res = await db.execute(sentiment_query)
    sentiment_counts = dict(sentiment_res.all())

    pos = sentiment_counts.get("positive", 0)
    neu = sentiment_counts.get("neutral", 0)
    neg = sentiment_counts.get("negative", 0)
    total_analyzed = pos + neu + neg or 1

    net_sentiment_idx = round(((pos - neg) / total_analyzed) * 100, 1)

    sentiment_summary = SentimentSummary(
        positive=pos,
        neutral=neu,
        negative=neg,
        total=total_posts,
        positive_percentage=round((pos / total_analyzed) * 100, 1),
        neutral_percentage=round((neu / total_analyzed) * 100, 1),
        negative_percentage=round((neg / total_analyzed) * 100, 1),
        net_sentiment_index=net_sentiment_idx,
    )

    # Emotions
    emotion_query = select(
        Sentiment.primary_emotion, func.count(Sentiment.id)
    ).group_by(Sentiment.primary_emotion)
    emotion_res = await db.execute(emotion_query)
    emotion_counts = dict(emotion_res.all())

    emotions_summary = EmotionSummary(
        anger=emotion_counts.get("anger", 0),
        anxiety=emotion_counts.get("anxiety", 0),
        sadness=emotion_counts.get("sadness", 0),
        hope=emotion_counts.get("hope", 0),
        neutral=emotion_counts.get("neutral", 0),
    )

    # Fetch all posts with sentiments for factual aggregation
    posts_query = select(
        Post.content,
        Post.likes_count,
        Post.author_username,
        Sentiment.locations,
        Sentiment.entities,
        Sentiment.sentiment_label,
    ).outerjoin(Sentiment, Post.id == Sentiment.post_id)
    posts_res = await db.execute(posts_query)
    all_post_rows = posts_res.all()

    loc_freq: Dict[str, Dict[str, int]] = {}
    ent_freq: Dict[str, Dict[str, int]] = {}

    # Define factual regional buckets matching Indonesian geographic realities
    regional_buckets = {
        "DKI Jakarta & Jabodetabek": {
            "keywords": ["jakarta", "bogor", "depok", "tangerang", "bekasi"],
            "cities": ["Jakarta Pusat", "Bogor", "Depok", "Tangerang", "Bekasi"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Jawa Barat": {
            "keywords": ["bandung", "cimahi", "cirebon", "tasikmalaya", "sukabumi", "karawang"],
            "cities": ["Kota Bandung", "Cirebon", "Tasikmalaya"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Jawa Tengah & DIY": {
            "keywords": ["semarang", "solo", "surakarta", "yogyakarta", "jogja", "magelang", "purwokerto"],
            "cities": ["Kota Semarang", "Yogyakarta", "Solo"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Jawa Timur": {
            "keywords": ["surabaya", "malang", "sidoarjo", "banyuwangi", "jember", "kediri"],
            "cities": ["Surabaya", "Malang", "Sidoarjo"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Sumatera Utara & Aceh": {
            "keywords": ["medan", "sumut", "aceh", "banda aceh", "binjai"],
            "cities": ["Medan", "Banda Aceh", "Binjai"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Riau & Sumatera Barat": {
            "keywords": ["riau", "pekanbaru", "pelalawan", "dumai", "padang", "sumbar", "batam"],
            "cities": ["Pekanbaru", "Padang", "Batam"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Sumatera Bagian Selatan": {
            "keywords": ["palembang", "sumsel", "jambi", "lampung", "bengkulu", "oki"],
            "cities": ["Palembang", "Jambi", "Bandar Lampung"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Kalimantan Barat": {
            "keywords": ["pontianak", "kalbar", "kubu raya", "ketapang"],
            "cities": ["Pontianak", "Kubu Raya", "Ketapang"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Kalimantan Tengah & Selatan": {
            "keywords": ["palangkaraya", "kalteng", "kotawaringin", "sebangau", "sampit", "banjarmasin", "kalsel", "banjarbaru"],
            "cities": ["Palangka Raya", "Banjarmasin", "Sampit", "Banjarbaru"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Kalimantan Timur & IKN": {
            "keywords": ["balikpapan", "samarinda", "kaltim", "ikn", "nusantara"],
            "cities": ["Balikpapan", "Samarinda", "Nusantara"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Sulawesi": {
            "keywords": ["makassar", "sulsel", "manado", "sulut", "palu", "sulteng", "kendari", "gorontalo"],
            "cities": ["Makassar", "Manado", "Palu"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Bali & Nusa Tenggara": {
            "keywords": ["denpasar", "bali", "badung", "mataram", "lombok", "kupang"],
            "cities": ["Denpasar", "Mataram", "Kupang"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Papua & Maluku": {
            "keywords": ["papua", "merauke", "jayawijaya", "maima", "jayapura", "ambon", "maluku", "sorong"],
            "cities": ["Jayapura", "Merauke", "Kota Ambon"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
        "Nasional & Komunitas Daring": {
            "keywords": ["nasional", "warganet", "indonesia", "medsos", "netizen", "publik"],
            "cities": ["Seluruh Indonesia", "Komunitas Daring"],
            "posts": [],
            "neg": 0,
            "issues": set(),
        },
    }

    for content, likes, username, locs, ents, sent in all_post_rows:
        text_lower = (content or "").lower()

        # Top locations parsing
        if locs:
            for loc in locs:
                if not loc:
                    continue
                loc_freq.setdefault(loc, {"total": 0, "neg": 0})
                loc_freq[loc]["total"] += 1
                if sent == "negative":
                    loc_freq[loc]["neg"] += 1

        # Top entities parsing
        if ents:
            for ent in ents:
                if not ent:
                    continue
                ent_freq.setdefault(ent, {"total": 0, "neg": 0})
                ent_freq[ent]["total"] += 1
                if sent == "negative":
                    ent_freq[ent]["neg"] += 1

        # Match to factual regional bucket
        matched_any = False
        for reg_name, reg_data in regional_buckets.items():
            if reg_name == "Nasional & Komunitas Daring":
                continue
            if any(k in text_lower for k in reg_data["keywords"]) or any(
                k.lower() in [l.lower() for l in (locs or [])] for k in reg_data["keywords"]
            ):
                matched_any = True
                reg_data["posts"].append((likes, content, username))
                if sent == "negative":
                    reg_data["neg"] += 1

                # Detect dynamic issues from content and entities
                if ents:
                    for ent in ents[:2]:
                        if ent and len(ent) > 2:
                            clean_ent = ent.lstrip("#")
                            reg_data["issues"].add(clean_ent)

                if any(w in text_lower for w in ["kebijakan", "aturan", "regulasi", "pemerintah", "dpr", "pemda", "transparan"]):
                    reg_data["issues"].add("Kritik Kebijakan & Transparansi")
                if any(w in text_lower for w in ["edukasi", "sosialisasi", "literasi", "pemahaman", "komunitas"]):
                    reg_data["issues"].add("Edukasi Publik & Komunitas")
                if any(w in text_lower for w in ["dampak", "rugi", "mahal", "biaya", "harga", "ekonomi"]):
                    reg_data["issues"].add("Dampak Finansial & Beban Warga")
                if any(w in text_lower for w in ["layanan", "fasilitas", "infrastruktur", "akses", "aplikasi", "sistem"]):
                    reg_data["issues"].add("Kesiapan Layanan & Fasilitas")
                if any(w in text_lower for w in ["keren", "apresiasi", "salut", "alhamdulillah", "terima kasih", "bangga", "optimis"]):
                    reg_data["issues"].add("Apresiasi & Respons Positif")
                if any(w in text_lower for w in ["evaluasi", "usut", "tanggung jawab", "tindak", "investigasi", "audit"]):
                    reg_data["issues"].add("Tuntutan Evaluasi & Akuntabilitas")
                if any(w in text_lower for w in ["viral", "ramai", "sorotan", "perbincangan", "netizen", "warganet"]):
                    reg_data["issues"].add("Sorotan Percakapan Viral")

                # Environmental / Disaster specific themes if relevant
                if "ispu" in text_lower or "tidak sehat" in text_lower:
                    reg_data["issues"].add("ISPU Sangat Tidak Sehat")
                if "kuning" in text_lower or "pekat" in text_lower:
                    reg_data["issues"].add("Kabut Asap Pekat")
                if "titik api" in text_lower or "gambut" in text_lower:
                    reg_data["issues"].add("Titik Api Lahan Gambut")
                if "sekolah" in text_lower or "daring" in text_lower:
                    reg_data["issues"].add("Sekolah Diliburkan/Daring")
                if "ispa" in text_lower or "sesak" in text_lower or "paru" in text_lower:
                    reg_data["issues"].add("Keluhan ISPA & Sesak Napas")
                if "padam" in text_lower or "air" in text_lower or "manggala" in text_lower:
                    reg_data["issues"].add("Operasi Pemadaman Satgas")

        if not matched_any:
            nat_data = regional_buckets["Nasional & Komunitas Daring"]
            nat_data["posts"].append((likes, content, username))
            if sent == "negative":
                nat_data["neg"] += 1
            if ents:
                for ent in ents[:2]:
                    if ent and len(ent) > 2:
                        nat_data["issues"].add(ent.lstrip("#"))
            nat_data["issues"].add("Diskusi Opini Publik")

    # Build regional reports list
    regional_reports: List[RegionalFactReport] = []
    for reg_name, reg_data in regional_buckets.items():
        total_p = len(reg_data["posts"])
        if total_p == 0:
            continue
        neg_ratio = round((reg_data["neg"] / total_p) * 100, 1)

        # Determine severity status
        if neg_ratio >= 65 and total_p >= 3:
            status = "Kritis"
        elif total_p >= 2:
            status = "Waspada"
        else:
            status = "Terkendali"

        # Best representative citizen voice quote (highest engagement)
        reg_data["posts"].sort(key=lambda x: x[0], reverse=True)
        top_post = reg_data["posts"][0]
        sample_quote = f"\"{top_post[1][:120]}...\" — @{top_post[2]}"

        issues_list = list(reg_data["issues"])[:4]
        if not issues_list:
            issues_list = ["Diskusi Komunitas Publik", "Aspirasi Warga Terkini"]

        regional_reports.append(
            RegionalFactReport(
                region_name=reg_name,
                status=status,
                total_reports=total_p,
                negative_percentage=neg_ratio,
                key_issues=issues_list,
                sample_citizen_voice=sample_quote,
                affected_cities=reg_data["cities"][:3],
            )
        )

    # Sort regional reports: Kritis first, then by report count
    status_order = {"Kritis": 0, "Waspada": 1, "Terkendali": 2}
    regional_reports.sort(key=lambda x: (status_order.get(x.status, 3), -x.total_reports))

    top_locations = [
        EntityMetric(
            name=k,
            count=v["total"],
            negative_ratio=round(v["neg"] / v["total"], 2) if v["total"] else 0,
        )
        for k, v in sorted(loc_freq.items(), key=lambda x: x[1]["total"], reverse=True)[:6]
    ]

    top_entities = [
        EntityMetric(
            name=k,
            count=v["total"],
            negative_ratio=round(v["neg"] / v["total"], 2) if v["total"] else 0,
        )
        for k, v in sorted(ent_freq.items(), key=lambda x: x[1]["total"], reverse=True)[:6]
    ]

    return OverviewMetrics(
        total_posts=total_posts,
        sentiment=sentiment_summary,
        emotions=emotions_summary,
        top_locations=top_locations,
        top_entities=top_entities,
        regional_reports=regional_reports,
        total_likes=total_likes,
        total_replies=total_replies,
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/timeline", response_model=List[TimelinePoint])
async def get_timeline(
    granularity: str = Query("hour", pattern="^(hour|day)$", description="'hour' or 'day'"),
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns time-series sentiment data aggregated by hour or day.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    bucket_fn = func.date_trunc('hour' if granularity == 'hour' else 'day', Post.posted_at)

    query = (
        select(
            bucket_fn.label("time_bucket"),
            func.coalesce(
                func.sum(case((Sentiment.sentiment_label == "positive", 1), else_=0)), 0
            ).label("positive"),
            func.coalesce(
                func.sum(case((Sentiment.sentiment_label == "neutral", 1), else_=0)), 0
            ).label("neutral"),
            func.coalesce(
                func.sum(case((Sentiment.sentiment_label == "negative", 1), else_=0)), 0
            ).label("negative"),
            func.count(Post.id).label("total"),
        )
        .outerjoin(Sentiment, Post.id == Sentiment.post_id)
        .where(Post.posted_at >= cutoff)
        .group_by("time_bucket")
        .order_by("time_bucket")
    )

    res = await db.execute(query)
    points = []
    for bucket, pos, neu, neg, total in res.all():
        if not bucket:
            continue

        if granularity == "hour":
            iso_str = bucket.strftime("%Y-%m-%d %H:00")
            display_label = bucket.strftime("%d %b %H:%M")
        else:
            iso_str = bucket.strftime("%Y-%m-%d")
            display_label = bucket.strftime("%d %b")

        net = round(((pos - neg) / total) * 100, 1) if total > 0 else 0.0

        points.append(
            TimelinePoint(
                timestamp=iso_str,
                display_label=display_label,
                positive=pos,
                neutral=neu,
                negative=neg,
                total=total,
                net_score=net,
            )
        )
    return points

import json
import logging
import re
from typing import List, Dict, Optional
from app.core.config import settings
from app.schemas.post import PostCreate
from app.schemas.sentiment import ThreadSentimentExtraction, GeminiBatchSentimentOutput

logger = logging.getLogger(__name__)


class SentimentService:
    """
    Sentiment and Entity Extraction Service for Indonesian Karhutla Threads.
    Uses Gemini Flash with Structured Outputs when GEMINI_API_KEY is available,
    with an intelligent Indonesian heuristic analyzer as zero-configuration fallback.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Gemini Flash client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")

    async def analyze_posts(
        self, posts: List[PostCreate]
    ) -> Dict[str, ThreadSentimentExtraction]:
        """
        Analyze sentiment, emotions, and extract locations/entities for a batch of posts.
        Routes to IndoBERT (recommended for Indonesian slang/code-mixing), Gemini, or fallback.
        """
        if not posts:
            return {}

        engine = (settings.SENTIMENT_ENGINE or "indobert").lower()
        logger.info(f"Analyzing {len(posts)} posts using sentiment engine: '{engine}'")

        # 1. Primary: IndoBERT Engine (Local, highly accurate on Indonesian text & slang)
        if engine == "indobert":
            try:
                from app.services.indobert_service import indobert_service
                return indobert_service.analyze_posts_batch(posts)
            except Exception as e:
                logger.error(
                    f"IndoBERT analysis failed: {e}. Falling back to next available engine.",
                    exc_info=True,
                )

        # 2. Secondary: Gemini LLM Engine
        if (engine == "gemini" or engine == "hybrid") and self.client:
            try:
                return await self._analyze_with_gemini(posts)
            except Exception as e:
                logger.warning(
                    f"Gemini API analysis failed ({e}). Falling back to Indonesian heuristic analyzer."
                )

        # 3. Fallback: Intelligent Heuristics
        return self._analyze_with_heuristics(posts)

    async def _analyze_with_gemini(
        self, posts: List[PostCreate]
    ) -> Dict[str, ThreadSentimentExtraction]:
        from google.genai import types

        results: Dict[str, ThreadSentimentExtraction] = {}
        chunk_size = 20

        for i in range(0, len(posts), chunk_size):
            chunk = posts[i : i + chunk_size]
            prompt_items = []
            for p in chunk:
                prompt_items.append(
                    f"- [Post ID: {p.id}] Penulis: @{p.author_username}\n  Teks: \"{p.content}\""
                )

            prompt_text = (
                "Anda adalah pakar analisis sentimen dan intelijen opini media sosial di Indonesia. "
                "Analisis kumpulan postingan Threads berikut secara mendalam, objektif, dan faktual mengenai topik yang dibahas "
                "(baik terkait isu sosial, teknologi, kebijakan publik, bencana lingkungan, olahraga, maupun peristiwa viral).\n\n"
                "Untuk setiap postingan, tentukan:\n"
                "1. sentiment: 'positive' (jika ada apresiasi, kepuasan, berita baik, keberhasilan), "
                "'neutral' (jika laporan data, pengumuman, fakta objektif, informasi netral), atau "
                "'negative' (jika ada keluhan, kritik, kecaman, keresahan, kerugian, atau kekecewaan).\n"
                "2. confidence: float (0.0 - 1.0).\n"
                "3. emotion: 'anger', 'anxiety', 'sadness', 'hope', atau 'neutral'.\n"
                "4. locations: daftar nama daerah/kota/provinsi di Indonesia yang disebut (misal: Jakarta, Bandung, Surabaya, Riau, Palangkaraya, dll).\n"
                "5. entities: daftar instansi/organisasi/isu/subjek utama yang disebut (misal: Pemerintah, DPR, BMKG, Kominfo, PSSI, BUMN, dll).\n"
                "6. summary_reason: penjelasan ringkas 1 kalimat alasan klasifikasi.\n\n"
                "DAFTAR POSTINGAN:\n"
                + "\n".join(prompt_items)
            )

            try:
                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt_text,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=GeminiBatchSentimentOutput,
                        temperature=0.2,
                    ),
                )
                if response.text:
                    data = json.loads(response.text)
                    batch = GeminiBatchSentimentOutput.model_validate(data)
                    for item in batch.results:
                        results[item.post_id] = item
            except Exception as e:
                logger.warning(f"Error analyzing chunk {i}-{i+chunk_size} with Gemini ({e}). Will use heuristic fallback for this batch.")

        # Ensure all posts in input are covered
        for p in posts:
            if p.id not in results:
                results[p.id] = self._analyze_single_heuristic(p)

        return results

    def _analyze_with_heuristics(
        self, posts: List[PostCreate]
    ) -> Dict[str, ThreadSentimentExtraction]:
        results: Dict[str, ThreadSentimentExtraction] = {}
        for p in posts:
            results[p.id] = self._analyze_single_heuristic(p)
        return results

    def _analyze_single_heuristic(self, post: PostCreate) -> ThreadSentimentExtraction:
        text = post.content.lower()

        # Location dictionary (National coverage)
        provinces_and_cities = [
            "jakarta", "bogor", "depok", "tangerang", "bekasi", "bandung", "surabaya",
            "semarang", "yogyakarta", "jogja", "solo", "surakarta", "malang", "cirebon",
            "medan", "padang", "palembang", "pekanbaru", "riau", "jambi", "lampung", "aceh",
            "batam", "pontianak", "banjarmasin", "banjarbaru", "palangkaraya", "kalteng", "kalbar",
            "kalsel", "kaltim", "balikpapan", "samarinda", "kotawaringin", "pelalawan", "rokan hilir",
            "kubu raya", "sebangau", "sampit", "makassar", "manado", "bali", "denpasar", "lombok",
            "mataram", "jayapura", "merauke", "papua", "ambon"
        ]
        found_locations_set = {
            loc.capitalize() for loc in provinces_and_cities if loc in text
        }
        if post.raw_metadata and post.raw_metadata.get("city"):
            found_locations_set.add(post.raw_metadata["city"])
        found_locations = list(found_locations_set)

        # Entity dictionary
        entity_keywords = {
            "klhk": "KLHK",
            "bmkg": "BMKG",
            "bnpb": "BNPB",
            "bpbd": "BPBD",
            "manggala agni": "Manggala Agni",
            "damkar": "Pemadam Kebakaran",
            "pemerintah": "Pemerintah",
            "pemda": "Pemerintah Daerah",
            "dpr": "DPR RI",
            "kemenkeu": "Kemenkeu",
            "kominfo": "Kominfo",
            "bumn": "BUMN",
            "sawit": "Industri Sawit",
            "korporasi": "Korporasi",
            "ispa": "ISPA",
            "ispu": "ISPU",
            "sekolah": "Sekolah Diliburkan",
            "water bombing": "Water Bombing",
            "masker": "Bantuan Masker",
            "ai": "Artificial Intelligence",
            "timnas": "Timnas Indonesia",
            "whoosh": "Kereta Cepat Whoosh",
            "ikn": "IKN Nusantara",
        }
        found_entities_set = {
            v for k, v in entity_keywords.items() if k in text
        }
        # Extract hashtags
        hashtags = re.findall(r"#([a-zA-Z0-9_]+)", post.content)
        for ht in hashtags[:3]:
            if len(ht) > 2:
                found_entities_set.add(f"#{ht}")
        found_entities = list(found_entities_set)

        # Negative indicators
        neg_words = [
            "pekat", "perih", "sesak", "gatal", "parah", "miris", "marah", "kecewa",
            "terbakar", "bau sangit", "bahaya", "sakit", "menyeramkan", "tidak sehat",
            "zona merah", "tolong", "darurat", "tangkap", "dalang", "tersiksa", "darurat asap",
            "buruk", "jelek", "rugi", "rusak", "gagal", "mahal", "bohong", "lambat", "muak", "hancur", "komplain"
        ]
        # Positive indicators
        pos_words = [
            "alhamdulillah", "hujan", "padam", "berhasil", "berkurang", "senang",
            "apresiasi", "terima kasih", "bersih", "membaik", "deras", "bantuan", "salut",
            "keren", "hebat", "mantap", "bagus", "bangga", "sukses", "juara", "puas", "rekomendasi", "optimis"
        ]
        # Neutral indicators
        neu_words = ["pantauan", "laporan", "merilis", "terpantau", "data", "satelit", "informasi", "update", "jadwal", "berita", "fakta"]

        neg_score = sum(1 for w in neg_words if w in text)
        pos_score = sum(1 for w in pos_words if w in text)
        neu_score = sum(1 for w in neu_words if w in text)

        kw = (post.raw_metadata or {}).get("keyword")
        is_karhutla = (
            any(w in text for w in ["karhutla", "kabut asap", "titik api", "asap pekat", "gambut", "bau sangit", "perih"])
            or (kw and any(w in kw.lower() for w in ["karhutla", "kabut asap", "asap", "kebakaran"]))
        )

        if pos_score > neg_score and pos_score >= 1:
            sentiment = "positive"
            emotion = "hope"
            confidence = 0.85
            if is_karhutla:
                summary = "Apresiasi terhadap bantuan/hujan yang meredakan kobaran karhutla."
            else:
                topic_title = kw.title() if kw else "topik"
                summary = f"Apresiasi, antusiasme, atau tanggapan positif publik seputar {topic_title}."
        elif neg_score >= pos_score and neg_score >= 1:
            sentiment = "negative"
            emotion = "anger" if any(w in text for w in ["marah", "tangkap", "dalang", "korporasi", "miris", "muak", "kecewa"]) else "anxiety"
            confidence = 0.90
            if is_karhutla:
                summary = "Keluhan dampak buruk kabut asap karhutla dan gangguan kesehatan."
            else:
                topic_title = kw.title() if kw else "topik"
                summary = f"Keluhan publik, kritik, atau kekhawatiran warganet terkait {topic_title}."
        else:
            sentiment = "neutral"
            emotion = "neutral"
            confidence = 0.75
            if is_karhutla:
                summary = "Laporan data faktual, pemantauan hotspot, atau berita umum."
            else:
                topic_title = kw.title() if kw else "topik"
                summary = f"Pemberitaan faktual, opini berimbang, atau informasi umum mengenai {topic_title}."

        return ThreadSentimentExtraction(
            post_id=post.id,
            sentiment=sentiment,
            confidence=confidence,
            emotion=emotion,
            locations=found_locations,
            entities=found_entities,
            summary_reason=summary,
        )


sentiment_service = SentimentService()

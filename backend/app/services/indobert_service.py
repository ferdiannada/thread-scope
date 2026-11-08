import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.schemas.post import PostCreate
from app.schemas.sentiment import ThreadSentimentExtraction
from app.services.normalizer import TextNormalizer

logger = logging.getLogger(__name__)


class IndoBERTService:
    """
    Dedicated IndoBERT Sentiment Analysis Engine for Indonesian Threads Posts.
    Uses Hugging Face Transformers model fine-tuned on Indonesian social media (IndoNLU SMSA).
    Optimized for CPU execution with batch processing and code-mixing text normalization.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.INDOBERT_MODEL_NAME
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self._is_loaded = False
        self.label_map = {
            0: "positive",
            1: "neutral",
            2: "negative",
        }

    def _ensure_loaded(self):
        """Loads model and tokenizer lazily on first inference to optimize startup time."""
        if self._is_loaded:
            return

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            # Optimize PyTorch CPU threading
            torch.set_num_threads(4)

            logger.info(f"Loading IndoBERT model: {self.model_name} on {self.device}...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, local_files_only=True)
            except Exception:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

            self.model.to(self.device)
            self.model.eval()

            # Detect label mapping from model config
            if hasattr(self.model.config, "id2label") and self.model.config.id2label:
                config_id2label = self.model.config.id2label
                parsed_map = {}
                for idx, raw_label in config_id2label.items():
                    idx_int = int(idx)
                    lbl_lower = str(raw_label).lower()
                    if "pos" in lbl_lower:
                        parsed_map[idx_int] = "positive"
                    elif "neg" in lbl_lower:
                        parsed_map[idx_int] = "negative"
                    elif "neu" in lbl_lower:
                        parsed_map[idx_int] = "neutral"
                    elif "label_0" in lbl_lower:
                        parsed_map[idx_int] = "positive"
                    elif "label_1" in lbl_lower:
                        parsed_map[idx_int] = "neutral"
                    elif "label_2" in lbl_lower:
                        parsed_map[idx_int] = "negative"
                    else:
                        parsed_map[idx_int] = lbl_lower
                if len(parsed_map) >= 3:
                    self.label_map = parsed_map

            self._is_loaded = True
            logger.info(f"IndoBERT model loaded successfully with label mapping: {self.label_map}")
        except Exception as e:
            logger.error(f"Failed to load IndoBERT model '{self.model_name}': {e}", exc_info=True)
            raise e

    def predict_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Runs batch prediction over a list of raw text inputs.
        Returns a list of dicts: {'sentiment': str, 'confidence': float, 'probabilities': dict}
        """
        if not texts:
            return []

        self._ensure_loaded()
        import torch

        # Normalize texts to clean slang and code-mixing
        normalized_texts = [TextNormalizer.clean_text(t) for t in texts]

        results = []
        batch_size = 16

        for i in range(0, len(normalized_texts), batch_size):
            chunk = normalized_texts[i : i + batch_size]
            # Replace empty strings with a neutral placeholder
            safe_chunk = [t if t.strip() else "kondisi normal" for t in chunk]

            inputs = self.tokenizer(
                safe_chunk,
                padding=True,
                truncation=True,
                max_length=128,
                return_tensors="pt",
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)

            for j in range(len(safe_chunk)):
                probs = probabilities[j].cpu().tolist()
                top_idx = int(torch.argmax(probabilities[j]).item())
                top_prob = probs[top_idx]
                sentiment_label = self.label_map.get(top_idx, "neutral")

                # Probabilities breakdown
                prob_breakdown = {}
                for idx, p in enumerate(probs):
                    lbl = self.label_map.get(idx, f"label_{idx}")
                    prob_breakdown[lbl] = round(p, 4)

                results.append({
                    "sentiment": sentiment_label,
                    "confidence": round(float(top_prob), 4),
                    "probabilities": prob_breakdown,
                    "normalized_text": chunk[j],
                })

        return results

    @classmethod
    def detect_sarcasm(cls, raw_text: str) -> bool:
        """
        Deteksi komprehensif pola sarkasme, sindiran, dan ironi retoris warganet Indonesia:
        1. Pujian semu diikuti klausul kontras/kekecewaan (misal: 'keren banget... tapi malah hancur').
        2. Pujian semu disandingkan langsung dengan kata kegagalan/kerusakan/masalah/bencana.
        3. Ucapan terima kasih semu atas hal negatif.
        4. Sikap pasif/abai saat kondisi krisis/warga komplain.
        5. Ejekan kepura-puraan / retorika kosong (membadut, lawak, dagelan, pencitraan, wacana doang).
        6. Emoji sarkas/ejekan (🤡, 🙄, 💀).
        """
        t = raw_text.lower()
        import re

        patterns = [
            # Pola 1: Pujian semu + kata hubung kontras / kenyataan di lapangan
            r"\b(keren|mantap|hebat|top|juara|terbaik|luar biasa|cakep|ciamik|salut|apresiasi)\b.*\b(padahal|tapi|malah|bukannya|sedangkan|nyatanya|faktanya|giliran|pas)\b",
            # Pola 2: Pujian semu + kata kegagalan/masalah/kerusakan/kekecewaan
            r"\b(keren|mantap|hebat|top|juara|luar biasa|bagus|ciamik)\b.*\b(crash|rusak|jebol|zonk|boncos|hancur|ampas|lelet|lemot|macet|antre|rugi|mahal|bohong|tipu|korupsi|gagal|bencana|krisis|derita|tersiksa|korban|blunder|sampah|polusi|asap|kebakaran|ispa)\b",
            # Pola 3: Ucapan terima kasih semu
            r"\b(makasih|terima kasih|thank you|trims)\b.*\b(bikin susah|merugikan|bikin kecewa|buang waktu|bikin emosi|bikin darah tinggi|racun|rusak|hancur|kapok)\b",
            # Pola 4: Sikap pasif pihak berwenang di tengah krisis
            r"\b(santai|diam|tidur|cuek|adem|tutup mata|pura-pura)\b.*\b(padahal|saat|ketika|waktu|di saat)\b.*\b(krisis|darurat|rusak|parah|bencana|korban|menjerit|ricuh|masalah|komplain|kebakaran|asap)\b",
            # Pola 5: Ejekan kepura-puraan / retorika kosong
            r"\b(membadut|dagelan|lawak|drama|pencitraan|cari panggung|narasi manis|wacana doang|janji manis|omon-omon|omong kosong)\b",
            # Pola 6: Emoji sarkas
            r"(🤡|🙄|💀|👏\s*🙃)",
            # Pola 7: Pujian semu + kritik normatif / birokrasi / lempar tanggung jawab
            r"\b(keren|mantap|hebat|top|juara|luar biasa|bagus|ciamik|salut)\b.*\b(serba normatif|lempar tanggung jawab|formalitas|drama|sandiwara|basa-basi|buang badan|alibi|pencitraan|omong kosong|dagelan|lawak|bisa ditebak|gak ada yang peduli|gak guna|zonk|hukum tumpul|sandiwara)\b",
            # Pola 8: Retorika sarkas sindiran publik & hukum
            r"\b(bisa ditebak lah ya|mau sampai kapan|bisa-bisanya|lucu banget liat|hebat ya|mantap betul|keren banget ya)\b.*\b(rakyat|warga|masyarakat|publik|hukum|sidang|pengadilan|keadilan|elit)\b",
        ]
        return any(re.search(p, t) for p in patterns)

    def extract_full_analysis(self, post: PostCreate) -> ThreadSentimentExtraction:
        """Helper for single post analysis."""
        return self.analyze_posts_batch([post])[post.id]

    def analyze_posts_batch(self, posts: List[PostCreate]) -> Dict[str, ThreadSentimentExtraction]:
        """
        Performs high-performance batch extraction for all posts:
        1. Single/chunked forward pass via IndoBERT.
        2. Disaster entities & location extraction via gazetteer.
        3. Contextual emotion & summary reason synthesis.
        """
        if not posts:
            return {}

        texts = [p.content for p in posts]
        predictions = self.predict_batch(texts)

        # 1. Location Gazetteer (Major Provinces & Cities Across Indonesia)
        location_mapping = {
            "jakarta": "Jakarta",
            "bogor": "Bogor",
            "depok": "Depok",
            "tangerang": "Tangerang",
            "bekasi": "Bekasi",
            "bandung": "Bandung",
            "surabaya": "Surabaya",
            "semarang": "Semarang",
            "yogyakarta": "Yogyakarta",
            "jogja": "Yogyakarta",
            "solo": "Solo",
            "surakarta": "Solo",
            "malang": "Malang",
            "cirebon": "Cirebon",
            "tasikmalaya": "Tasikmalaya",
            "sukabumi": "Sukabumi",
            "serang": "Serang",
            "banten": "Banten",
            "banyuwangi": "Banyuwangi",
            "jember": "Jember",
            "kediri": "Kediri",
            "medan": "Medan",
            "padang": "Padang",
            "palembang": "Palembang",
            "pekanbaru": "Pekanbaru",
            "riau": "Riau",
            "jambi": "Jambi",
            "lampung": "Lampung",
            "aceh": "Aceh",
            "batam": "Batam",
            "bengkulu": "Bengkulu",
            "pelalawan": "Pelalawan",
            "dumai": "Dumai",
            "pontianak": "Pontianak",
            "banjarmasin": "Banjarmasin",
            "banjarbaru": "Banjarbaru",
            "palangkaraya": "Palangkaraya",
            "balikpapan": "Balikpapan",
            "samarinda": "Samarinda",
            "kalteng": "Kalimantan Tengah",
            "kalbar": "Kalimantan Barat",
            "kalsel": "Kalimantan Selatan",
            "kaltim": "Kalimantan Timur",
            "kotawaringin": "Kotawaringin",
            "sampit": "Sampit",
            "sebangau": "Sebangau",
            "ketapang": "Ketapang",
            "makassar": "Makassar",
            "manado": "Manado",
            "palu": "Palu",
            "kendari": "Kendari",
            "gorontalo": "Gorontalo",
            "denpasar": "Denpasar",
            "bali": "Bali",
            "mataram": "Mataram",
            "lombok": "Lombok",
            "kupang": "Kupang",
            "ambon": "Ambon",
            "jayapura": "Jayapura",
            "merauke": "Merauke",
            "papua": "Papua",
            "jaksel": "Jakarta Selatan",
            "jakpus": "Jakarta Pusat",
            "jakbar": "Jakarta Barat",
            "jaktim": "Jakarta Timur",
            "jakut": "Jakarta Utara",
            "bdg": "Bandung",
            "sby": "Surabaya",
            "pku": "Pekanbaru",
            "ptk": "Pontianak",
        }

        # 2. Entity Gazetteer
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
            "kemenkes": "Kemenkes",
            "kemendikbud": "Kemendikbud",
            "kominfo": "Kominfo",
            "bumn": "BUMN",
            "tni": "TNI",
            "polri": "Polri",
            "satgas": "Satgas",
            "kpk": "KPK",
            "kpu": "KPU",
            "bawaslu": "Bawaslu",
            "sawit": "Industri Sawit",
            "korporasi": "Korporasi / Perusahaan",
            "ispa": "ISPA",
            "ispu": "ISPU",
            "sekolah": "Sekolah Diliburkan",
            "water bombing": "Water Bombing",
            "masker": "Bantuan Masker",
            "helikopter": "Helikopter Water Bombing",
            "hujan buatan": "Teknologi Modifikasi Cuaca (TMC)",
            "tmc": "Teknologi Modifikasi Cuaca (TMC)",
            "ai": "Artificial Intelligence",
            "kecerdasan buatan": "Kecerdasan Buatan",
            "timnas": "Timnas Indonesia",
            "pssi": "PSSI",
            "whoosh": "Kereta Cepat Whoosh",
            "ikn": "IKN Nusantara",
            "pn jakarta pusat": "PN Jakarta Pusat",
            "pn jakpus": "PN Jakarta Pusat",
            "pengadilan": "Pengadilan",
            "sidang": "Persidangan",
            "mahkamah konstitusi": "Mahkamah Konstitusi",
            "mk": "Mahkamah Konstitusi",
            "ptun": "PTUN",
            "majelis hakim": "Majelis Hakim",
            "hakim": "Majelis Hakim",
            "jaksa": "Kejaksaan",
            "jokowi": "Joko Widodo",
            "gugatan": "Gugatan Hukum",
            "eksepsi": "Eksepsi Perkara",
            "advokat": "Tim Advokat",
            "kuasa hukum": "Kuasa Hukum",
        }

        results: Dict[str, ThreadSentimentExtraction] = {}
        import re

        for post, pred in zip(posts, predictions):
            sentiment = pred["sentiment"]
            confidence = pred["confidence"]
            text_lower = post.content.lower()

            # Pemeriksaan Sarkasme: Bila IndoBERT mendeteksi Positive namun teks mengandung sindiran sarkas
            is_sarcastic = self.detect_sarcasm(post.content)

            # Kalibrasi Konteks & Polaritas Nyata Warganet
            neg_markers = [
                "hancur", "rusak", "kecewa", "zonk", "boncos", "mengecewakan", "buruk", "parah",
                "rugi", "bobrok", "gagal", "muak", "marah", "blunder", "bencana", "sesak", "krisis",
                "penipuan", "scam", "bohong", "korupsi", "sakit", "ancur", "lelet", "lemot", "down",
                "kacau", "curang", "sampah", "jijik", "sengsara", "derita", "tersiksa", "darurat"
            ]
            pos_markers = [
                "alhamdulillah", "terima kasih banyak", "sangat puas", "rekomended", "recommended",
                "juara banget", "luar biasa", "sangat senang", "bangga banget", "sangat bagus",
                "sangat bersyukur", "terbaik", "salut banget", "bikin salut", "apresiasi setinggi-tingginya",
                "apresiasi", "solidaritas", "optimis", "gacor", "mantul", "juara", "bagus banget", "keren banget",
                "terang benderang", "integritas moral"
            ]

            # Deteksi negasi terhadap kata negatif (contoh: 'tidak pernah gagal', 'ga pernah gagal bikin salut')
            is_negated_failure = bool(re.search(r"\b(tidak|tak|gak|ga)\s+(pernah\s+)?(gagal|kecewa|mengecewakan|rugi)\b", text_lower))
            is_pos_intensifier = any(p in text_lower for p in ["mantul parah", "gacor parah", "keren parah", "bagus parah", "enak parah", "fix no debat", "tidak pernah gagal", "ga pernah gagal"])
            
            # Cek apakah ada penanda negatif yang bukan merupakan negasi positif
            has_strong_neg = any(
                w in text_lower for w in neg_markers 
                if (w != "parah" or not is_pos_intensifier) and (w != "gagal" or not is_negated_failure)
            )
            has_strong_pos = any(w in text_lower for w in pos_markers) or is_pos_intensifier

            if is_sarcastic:
                sentiment = "negative"
                confidence = max(0.92, confidence)
            elif sentiment == "positive" and has_strong_neg and not has_strong_pos:
                sentiment = "negative"
                confidence = max(0.88, confidence)
            elif sentiment == "negative" and has_strong_pos and not has_strong_neg:
                sentiment = "positive"
                confidence = max(0.88, confidence)

            found_locations_set = set()
            for loc_k, loc_name in location_mapping.items():
                if re.search(rf"\b{re.escape(loc_k)}\b", text_lower):
                    found_locations_set.add(loc_name)

            # Metadata fallback for location
            if post.raw_metadata and post.raw_metadata.get("city"):
                found_locations_set.add(post.raw_metadata["city"])

            found_locations = list(found_locations_set)

            found_entities_set = set()
            for k, v in entity_keywords.items():
                if re.search(rf"\b{re.escape(k)}\b", text_lower):
                    found_entities_set.add(v)

            # Hashtags as dynamic entities
            hashtags = re.findall(r"#([a-zA-Z0-9_]+)", post.content)
            for ht in hashtags[:3]:
                if len(ht) > 2:
                    found_entities_set.add(f"#{ht}")

            # Topic keyword as entity if mentioned
            kw = (post.raw_metadata or {}).get("keyword")
            if kw and kw.lower() in text_lower:
                found_entities_set.add(kw.title())

            found_entities = list(found_entities_set)

            # 3. Emotion Synthesis
            emotion = "neutral"
            if sentiment == "negative":
                if is_sarcastic or any(w in text_lower for w in ["marah", "tangkap", "dalang", "korporasi", "hukum", "bakar", "gila", "muak", "biadab", "bohong", "kecewa", "rusak", "parah", "benci"]):
                    emotion = "anger"
                elif any(w in text_lower for w in ["sesak", "kabut", "asap", "ispa", "pekat", "masker", "darurat", "bahaya", "takut", "cemas", "khawatir", "waspada", "ancaman", "panik"]):
                    emotion = "anxiety"
                elif any(w in text_lower for w in ["sedih", "menangis", "kasihan", "mati", "hancur", "miris", "pupus", "kasian", "sayang", "duka"]):
                    emotion = "sadness"
                else:
                    emotion = "anxiety"
            elif sentiment == "positive":
                emotion = "hope"
            else:
                emotion = "neutral"

            # 4. Contextual Summary Reason Synthesis
            kw = (post.raw_metadata or {}).get("keyword")
            is_karhutla = (
                any(w in text_lower for w in ["karhutla", "kabut asap", "titik api", "asap pekat", "gambut"])
                or (kw and any(w in kw.lower() for w in ["karhutla", "kabut asap", "asap", "kebakaran"]))
            )

            if is_karhutla:
                if sentiment == "positive":
                    summary = "Apresiasi atau kabar baik terkait hujan, pemadaman api, dan penurunan kabut asap."
                elif sentiment == "negative":
                    if is_sarcastic:
                        summary = "Sindiran sarkastik terhadap penanganan bencana, kelambanan respon, atau oknum pembakar."
                    elif emotion == "anger":
                        summary = "Kecaman publik terhadap pembakar hutan, kelalaian penegakan hukum, atau korporasi."
                    elif emotion == "sadness":
                        summary = "Keprihatinan mendalam atas kerusakan ekosistem flora/fauna dan penderitaan korban kabut asap."
                    else:
                        summary = "Keluhan dampak kabut asap pekat, sesak napas (ISPA), dan ancaman kesehatan."
                else:
                    summary = "Pemberitaan faktual, pemantauan hotspot BMKG/satelit, atau informasi netral seputar karhutla."
            else:
                topic_title = kw.title() if kw else "topik"
                if sentiment == "positive":
                    summary = f"Apresiasi, antusiasme, atau tanggapan positif publik seputar {topic_title}."
                elif sentiment == "negative":
                    if is_sarcastic:
                        summary = f"Sindiran bernada sarkas atau kritik tajam warganet seputar {topic_title}."
                    elif emotion == "anger":
                        summary = f"Kekesalan, protes keras, atau kecaman warganet terkait {topic_title}."
                    elif emotion == "sadness":
                        summary = f"Keprihatinan atau rasa kecewa mendalam warganet terkait dampak {topic_title}."
                    else:
                        summary = f"Keluhan publik, keresahan, atau ketidaknyamanan warganet seputar {topic_title}."
                else:
                    summary = f"Pemberitaan faktual, opini berimbang, atau informasi umum mengenai {topic_title}."

            results[post.id] = ThreadSentimentExtraction(
                post_id=post.id,
                sentiment=sentiment,
                confidence=confidence,
                emotion=emotion,
                locations=found_locations,
                entities=found_entities,
                summary_reason=summary,
            )

        return results


indobert_service = IndoBERTService()

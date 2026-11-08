import re
from typing import Dict

# Pemetaan emoji ke representasi semantik emosi/sentimen bahasa Indonesia yang dipahami Transformer
EMOJI_SENTIMENT_MAP: Dict[str, str] = {
    # Positif / Apresiasi / Antusiasme
    "🔥": " keren semangat luar biasa ",
    "👏": " apresiasi hebat salut ",
    "🙌": " bersyukur bahagia luar biasa ",
    "😍": " sangat suka kagum ",
    "🥰": " sangat senang suka ",
    "✨": " istimewa cemerlang indah ",
    "🚀": " maju pesat hebat ",
    "❤️": " cinta suka bangga ",
    "💖": " sangat suka senang ",
    "💯": " sempurna benar tepat ",
    "👍": " bagus setuju mantap ",
    "🏆": " juara terbaik pemenang ",
    "🎉": " selamat perayaan gembira ",
    "🤩": " sangat takjub kagum ",
    "💪": " kuat bersemangat tangguh ",
    "🙏": " berdoa terima kasih harap ",
    "😊": " tersenyum senang ramah ",
    "😁": " gembira senang ceria ",
    "😎": " hebat percaya diri keren ",
    "🤝": " kerja sama solidaritas sepakat ",

    # Negatif / Marah / Sarkasme / Muak
    "😡": " sangat marah geram ",
    "🤬": " sangat marah mengumpat ",
    "😤": " kesal marah jengkel ",
    "🤡": " badut konyol memalukan sarkas ",
    "💀": " mati konyol parah ",
    "☠️": " berbahaya mematikan buruk ",
    "🤮": " sangat jijik muak mual ",
    "🤢": " jijik mual enek ",
    "👎": " buruk jelek tidak setuju ",
    "🤦": " kecewa heran tepuk jidat ",
    "🤦‍♂️": " kecewa heran tepuk jidat ",
    "🤦‍♀️": " kecewa heran tepuk jidat ",
    "💩": " kotoran sangat buruk ampas ",
    "🙄": " mencibir malas sinis ",
    "😒": " sinis malas kesal ",
    "🖕": " kasar menghina sangat benci ",
    "🚫": " dilarang tolak bahaya ",

    # Cemas / Sedih / Duka / Keprihatinan
    "😭": " menangis sangat sedih menderita ",
    "😢": " sedih menangis terharu ",
    "🥺": " memelas sedih kasihan ",
    "💔": " patah hati sangat sedih kecewa ",
    "😰": " cemas takut khawatir panik ",
    "😨": " takut panik kaget ",
    "😱": " sangat terkejut takut panik ",
    "🥀": " layu duka nestapa ",
    "😣": " menderita sakit tersiksa ",
    "😞": " sangat kecewa murung sedih ",
    "😔": " murung bersedih kecewa ",
    "😩": " lelah tertekan frustrasi ",
    "😫": " sangat lelah frustrasi ",
    "⚠️": " peringatan bahaya waspada ",
    "🚨": " darurat bahaya waspada ",
}

# Pemetaan frasa multi-kata (idiom & slang sosmed Indonesia)
MULTI_WORD_MAP: Dict[str, str] = {
    "stay safe": "tetap aman dan waspada",
    "gabisa napas": "sesak napas tidak bisa bernapas",
    "sesek napas": "sesak napas",
    "parah bgt": "parah sekali",
    "for real": "sungguhan",
    "nir empati": "tidak punya empati kejam jahat",
    "nir-empati": "tidak punya empati kejam jahat",
    "nirempati": "tidak punya empati kejam jahat",
    "dibilang estetik": "dianggap remeh sebagai estetik",
    "ga kaleng-kaleng": "sangat bagus berkualitas hebat",
    "gak kaleng-kaleng": "sangat bagus berkualitas hebat",
    "bukan kaleng-kaleng": "sangat bagus berkualitas hebat",
    "worth it": "sangat sepadan memuaskan",
    "ga worth it": "tidak sepadan mengecewakan",
    "gak worth it": "tidak sepadan mengecewakan",
    "no debat": "pasti benar tidak terbantahkan terbaik",
    "fix no debat": "pasti benar tidak terbantahkan terbaik",
    "menyala abangku": "sangat hebat luar biasa bersemangat",
    "menyala abangkuh": "sangat hebat luar biasa bersemangat",
    "top markotop": "sangat bagus memuaskan sekali",
    "mantul parah": "mantap betul luar biasa",
    "gacor parah": "sangat hebat luar biasa",
    "keren parah": "sangat keren luar biasa",
    "enak parah": "sangat enak luar biasa",
    "bagus parah": "sangat bagus luar biasa",
    "lucu parah": "sangat lucu menghibur",
    "zonk parah": "sangat mengecewakan sia-sia gagal",
    "boncos parah": "rugi besar menghabiskan uang",
    "ancur lebur": "rusak parah hancur",
    "ancur parah": "rusak parah hancur",
    "red flag": "tanda bahaya sangat mencurigakan buruk",
    "green flag": "tanda baik sangat terpercaya",
    "bikin emosi": "membuat sangat kesal dan marah",
    "bikin kesel": "membuat sangat kesal dan marah",
    "bikin darah tinggi": "membuat sangat kesal dan marah",
    "ga habis pikir": "sangat heran bingung dan kecewa",
    "gak habis pikir": "sangat heran bingung dan kecewa",
    "jauh dari kata memuaskan": "sangat buruk tidak memuaskan mengecewakan",
    "kurang ajar": "sangat tidak sopan jahat",
    "minim respon": "lamban acuh tidak bertanggung jawab",
    "minim tindakan": "lamban acuh tidak bertanggung jawab",
    "nol prestasi": "gagal total tidak ada hasil",
    "nihil hasil": "gagal total tidak ada hasil",
    "omong kosong": "janji palsu bohong tanpa bukti",
    "omon omon": "janji palsu bohong tanpa bukti",
    "omon-omon": "janji palsu bohong tanpa bukti",
    "cari panggung": "mencari perhatian keuntungan pribadi",
    "panjat sosial": "mencari perhatian popularitas",
    "wacana doang": "hanya janji tanpa implementasi nyata",
    "narasi manis": "pencitraan kepura-puraan semu",
    "janji manis": "pencitraan kepura-puraan semu",
    "salah fokus": "salah perhatian",
    "turut berduka": "sangat sedih berbelasungkawa",
    "turut berbelasungkawa": "sangat sedih berbelasungkawa",
    "semoga lekas sembuh": "berdoa semoga segera pulih baik",
    "ga bisa dipungkiri": "fakta nyata terbukti",
    "tidak bisa dipungkiri": "fakta nyata terbukti",
    "tidak buruk": "cukup lumayan baik",
    "ga buruk": "cukup lumayan baik",
    "gak buruk": "cukup lumayan baik",
    "tidak mengecewakan": "sangat memuaskan bagus",
    "ga mengecewakan": "sangat memuaskan bagus",
    "gak mengecewakan": "sangat memuaskan bagus",
    "tidak ramah": "kasar tidak bersahabat",
    "ga ramah": "kasar tidak bersahabat",
    "tidak jelas": "kacau membingungkan tidak jelas",
    "ga jelas": "kacau membingungkan tidak jelas",
    "gajelas": "kacau membingungkan tidak jelas",
    "tidak berguna": "sia-sia tidak bermanfaat",
    "ga berguna": "sia-sia tidak bermanfaat",
    "ga guna": "sia-sia tidak bermanfaat",
}

# Kamus normalisasi slang, singkatan, dan code-mixing Indonesia-Inggris khas sosmed (Threads/Twitter/Instagram)
SLANG_MAP: Dict[str, str] = {
    # Partikel & Kata Hubung
    "yg": "yang",
    "yng": "yang",
    "dgn": "dengan",
    "sm": "sama",
    "dri": "dari",
    "dr": "dari",
    "krn": "karena",
    "karna": "karena",
    "tp": "tapi",
    "tpi": "tapi",
    "klo": "kalau",
    "kalo": "kalau",
    "kl": "kalau",
    "jg": "juga",
    "jga": "juga",
    "jd": "jadi",
    "jdi": "jadi",
    "utk": "untuk",
    "bt": "buat",
    "bwt": "buat",
    "dlm": "dalam",
    "bwh": "bawah",
    "ats": "atas",
    "stlh": "setelah",
    "sblm": "sebelum",
    
    # Kata Sifat & Keterangan Derajat
    "bgt": "banget",
    "bgtt": "banget",
    "bgtz": "banget",
    "bgtlah": "banget",
    "bet": "banget",
    "bat": "banget",
    "beut": "banget",
    "skrg": "sekarang",
    "skrng": "sekarang",
    "bener": "benar",
    "bnr": "benar",
    "beneran": "sungguhan",
    "parahh": "parah",
    "gilaa": "gila",
    "anjir": "parah",
    "anjr": "parah",
    "njir": "parah",
    "bjir": "parah",
    "anj": "parah",
    "goks": "hebat parah",
    "gokil": "hebat parah",
    "buset": "astaga parah",
    "busetdah": "astaga parah",
    
    # Negasi & Modalitas
    "ga": "tidak",
    "gak": "tidak",
    "nggak": "tidak",
    "ngga": "tidak",
    "g": "tidak",
    "tdk": "tidak",
    "tak": "tidak",
    "bkn": "bukan",
    "blm": "belum",
    "belom": "belum",
    "udh": "sudah",
    "udah": "sudah",
    "sdh": "sudah",
    "dah": "sudah",
    "bs": "bisa",
    "gbs": "tidak bisa",
    "gabisa": "tidak bisa",
    "gabisah": "tidak bisa",
    "gabisaa": "tidak bisa",
    "gaada": "tidak ada",
    "gakada": "tidak ada",
    "gada": "tidak ada",
    "gapapa": "tidak apa-apa",
    "gpp": "tidak apa-apa",
    "gamau": "tidak mau",
    "gakmau": "tidak mau",
    "gausah": "tidak perlu",
    "gakusah": "tidak perlu",
    "gausa": "tidak perlu",
    "gatau": "tidak tahu",
    "gatau-diri": "tidak tahu diri",
    "gapernah": "tidak pernah",
    
    # Pronomina (Subjek/Objek)
    "gw": "saya",
    "gue": "saya",
    "gua": "saya",
    "sy": "saya",
    "ak": "aku",
    "aq": "aku",
    "w": "saya",
    "lu": "kamu",
    "lo": "kamu",
    "loe": "kamu",
    "u": "kamu",
    "km": "kamu",
    "kmu": "kamu",
    "mrk": "mereka",
    "kt": "kita",
    "org": "orang",
    "warga": "masyarakat warga",
    "netizen": "warganet",
    
    # Emosi & Sentimen Populer (Positif)
    "mantul": "mantap betul sangat bagus",
    "gacor": "sangat hebat berprestasi",
    "ciamik": "sangat bagus indah",
    "top": "terbaik sangat bagus",
    "rekomended": "sangat disarankan berkualitas",
    "recommended": "sangat disarankan berkualitas",
    "respek": "sangat menghormati bangga",
    "respect": "sangat menghormati bangga",
    "salut": "sangat kagum bangga",
    "proud": "sangat bangga",
    "alhamd": "alhamdulillah",
    "alhamdulillah": "alhamdulillah bersyukur",
    "bersyukur": "alhamdulillah bersyukur",
    "bismillah": "semoga berkah dengan niat baik",
    "berkah": "sangat bermanfaat membawa berkah",
    
    # Emosi & Sentimen Populer (Negatif / Sarkasme / Kekecewaan)
    "kecewa": "sangat kecewa",
    "kzl": "sangat kesal marah",
    "kesel": "sangat kesal",
    "kezel": "sangat kesal",
    "emosi": "marah kesal",
    "gondok": "sangat jengkel kesal",
    "enek": "muak jijik",
    "eneg": "muak jijik",
    "muak": "sangat muak jijik",
    "geram": "sangat marah geram",
    "zonk": "kecewa gagal sia-sia",
    "boncos": "rugi besar sia-sia",
    "ampas": "sangat buruk tidak berguna",
    "lelet": "sangat lambat",
    "lemot": "sangat lambat tidak responsif",
    "ngebug": "bermasalah rusak sistemnya",
    "ngelag": "sangat lambat terhambat",
    "down": "rusak tidak dapat diakses",
    "crash": "rusak mendadak gagal",
    "ambyar": "hancur berantakan",
    "ngenes": "sangat sedih memprihatinkan",
    "nyesek": "sangat sedih sesak di dada",
    "mewek": "menangis bersedih",
    "miris": "sangat memprihatinkan menyedihkan",
    "lawak": "konyol tidak serius dagelan",
    "dagelan": "konyol tidak masuk akal",
    "membadut": "berperilaku konyol memalukan",
    "blunder": "kesalahan fatal ceroboh",
    "scam": "penipuan kriminal",
    "nipu": "membohongi menipu",
    "boong": "berbohong tidak benar",
    "hoax": "berita bohong palsu",
    
    # Keluhan Kesehatan & Kebencanaan
    "sesek": "sesak",
    "napas": "napas",
    "nafas": "napas",
    "gatel": "gatal",
    "pedihh": "perih",
    "perihh": "perih",
    "apinya": "api kebakaran",
    "asapnya": "kabut asap",
    "ispa": "infeksi saluran pernapasan",
    "ispu": "indeks pencemaran udara",
    
    # Permintaan, Harapan & Singkatan Umum
    "plis": "tolong",
    "pliss": "tolong",
    "pls": "tolong",
    "please": "tolong",
    "tlg": "tolong",
    "mhn": "mohon",
    "gws": "semoga lekas sembuh",
    "fyi": "sebagai informasi penting",
    "cmiiw": "koreksi jika saya salah",
    "tbh": "sejujurnya faktanya",
    "imo": "menurut pendapat saya",
    "imho": "menurut pandangan objektif saya",
    "pov": "sudut pandang nyata",
    "spill": "ungkap fakta sebenarnya",
    "salfok": "salah fokus teralihkan",
    "pansos": "mencari perhatian keuntungan",
    "caper": "mencari perhatian",
    "julid": "iri dengki mencibir",
    "baper": "terbawa perasaan sensitif",
    "mager": "malas bergerak tidak mau bertindak",
    "gabut": "tidak ada kegiatan",
    "halu": "berkhayal tidak realistis",
    "gaje": "tidak jelas kacau",
    "alay": "berlebihan norak",
    "lebay": "sangat berlebihan",
    "cringe": "memalukan menggelikan",
    "ilfil": "hilang rasa hormat muak",
    "ilfeel": "hilang rasa hormat muak",
    "toxic": "merusak beracun jahat",
}


class TextNormalizer:
    """
    Pra-pemrosesan teks percakapan Threads bahasa Indonesia:
    1. Membersihkan URL, mention (@user), dan mengekstrak hashtag.
    2. Mentranslasikan emoji visual ke deskriptor emosi bahasa Indonesia.
    3. Mengompresi karakter berulang (misal: 'kerennn' -> 'keren', 'paraaahhh' -> 'parah').
    4. Mengganti frasa idiom & multi-kata slang ke bentuk baku berkekuatan sentimen.
    5. Melakukan normalisasi singkatan slang & code-mixing ke bentuk baku ramah tokenizer IndoBERT.
    """

    @classmethod
    def clean_text(cls, text: str) -> str:
        if not text:
            return ""

        # 1. Hapus URL
        cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)

        # 2. Hapus mention (@username)
        cleaned = re.sub(r"@\w+", "", cleaned)

        # 3. Terjemahkan emoji ke representasi semantik emosi Indonesia
        for emoji_char, semantic_text in EMOJI_SENTIMENT_MAP.items():
            if emoji_char in cleaned:
                cleaned = cleaned.replace(emoji_char, semantic_text)

        # 4. Ubah hashtag (#TimnasDay -> TimnasDay, #Karhutla -> Karhutla)
        cleaned = re.sub(r"#(\w+)", r" \1 ", cleaned)

        # 5. Kompresi karakter berulang lebih dari 2 kali ('woyyy' -> 'woy', 'gilaaa' -> 'gila', 'mantaaap' -> 'mantap')
        cleaned = re.sub(r"(.)\1{2,}", r"\1", cleaned).lower()

        # 6. Ganti frasa multi-kata terlebih dahulu sebelum tokenisasi per kata
        for phrase, repl in MULTI_WORD_MAP.items():
            pattern = rf"\b{re.escape(phrase)}\b"
            cleaned = re.sub(pattern, repl, cleaned)

        # 7. Lowercase dan pemetaan slang per kata
        words = cleaned.split()
        normalized_words = [SLANG_MAP.get(w, w) for w in words]
        normalized = " ".join(normalized_words)

        # 8. Bersihkan spasi berlebih
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

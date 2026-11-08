# Dokumentasi Ilmiah dan Teknis Sistem: Karhutla Threads Scraping & Sentiment Intelligence

**Sistem Pengumpulan dan Intelijen Sentimen Percakapan Publik Meta Threads Terkait Krisis Kebakaran Hutan dan Lahan (Karhutla) di Indonesia**

---

## Ringkasan Eksekutif (Abstract)

Krisis Kebakaran Hutan dan Lahan (Karhutla) di Indonesia merupakan bencana lingkungan tahunan yang berdampak langsung terhadap kesehatan masyarakat, aktivitas ekonomi, dan kualitas udara lintas batas. Di tengah keterbatasan akses Application Programming Interface (API) terbuka pada platform media sosial pasca pembatasan komersial Twitter (X), platform Meta Threads menjadi salah satu kanal microblogging baru yang banyak digunakan masyarakat terdampak untuk menyampaikan laporan langsung, keluhan penyakit pernapasan, serta persepsi kebijakan pemerintah.

Dokumen ini menyajikan spesifikasi arsitektur, metodologi komputasi, dan evaluasi teknis dari sistem *Karhutla Threads Scraping & Sentiment Intelligence*. Sistem ini dirancang untuk melakukan akuisisi data otomatis secara nir-henti (*headless*), prapemrosesan teks percakapan informal, klasifikasi polaritas sentimen multi-tier (menggabungkan *fine-tuned* Transformer IndoBERT dan Large Language Model Gemini Flash), ekstraksi entitas geografis berbasis leksikon kebencanaan, serta visualisasi analitik interaktif berbasis SvelteKit dan PostgreSQL.

---

## 1. Pendahuluan

### 1.1 Latar Belakang
Pemantauan opini publik secara waktu-nyata (*real-time crisis monitoring*) memegang peranan krusial dalam manajemen bencana modern. Informasi lapangan dari masyarakat sering kali muncul mendahului laporan resmi stasiun pemantau Indeks Standar Pencemar Udara (ISPU) atau rilis badan penanggulangan bencana. 

Tantangan utama dalam pemantauan percakapan publik kontemporer adalah:
1. **Fragmentasi Platform**: Terjadinya migrasi pengguna dari Twitter ke Meta Threads.
2. **Ketiadaan API Akademis Terbuka**: Threads belum menyediakan akses pencarian publik bebas biaya yang setara dengan skema akademis terdahulu, menuntut strategi akuisisi data peramban (*browser automation*) yang tangguh.
3. **Karakteristik Teks Informal**: Percakapan di media sosial Indonesia kaya akan kata singkatan, istilah daerah, bahasa gaul (*slang*), dan pencampuran bahasa (*code-mixing* bahasa Indonesia dan Inggris).

### 1.2 Rumusan Masalah
1. Bagaimana merancang mekanisme pengumpulan data (*scraping*) yang andal, tahan terhadap deteksi bot, dan mampu mengekstrak metadata presisi dari Meta Threads?
2. Bagaimana memproses teks percakapan warga Indonesia yang sarat *slang* agar dapat dianalisis secara akurat oleh model Natural Language Processing (NLP)?
3. Bagaimana mengimplementasikan arsitektur inferensi sentimen dan ekstraksi entitas kebencanaan yang akurat dan memiliki mekanisme toleransi kegagalan (*fault-tolerant*)?
4. Bagaimana merancang antarmuka visualisasi data yang memenuhi standar keterbacaan teknis tanpa distorsi estetika yang berlebihan?

### 1.3 Batasan Masalah
- **Domain Kasus**: Isu Kebakaran Hutan dan Lahan (Karhutla), kabut asap, titik api (*hotspot*), dan dampaknya (ISPA, visibilitas, penanganan pemadaman) di Indonesia.
- **Sumber Data**: Postingan publik pada Meta Threads yang dapat diakses secara terbuka tanpa autentikasi kredensial pengguna privat.
- **Bahasa Korpus**: Bahasa Indonesia informal dan variasi *code-mixing* kontemporer.

### 1.4 Kebaruan Sistem (*Novelty*)
- **Snowflake ID Timestamp Decoding**: Rekayasa balik format 64-bit identifier pada Threads untuk mengekstrak stempel waktu UTC presisi tinggi tanpa bergantung pada representasi waktu relatif HTML.
- **Multi-Tier Hybrid Inference**: Integrasi berjenjang antara Transformer berbasis CPU lokal (IndoBERT SMSA) dan Zero-Shot LLM (Gemini 2.5 Flash) dengan proteksi *heuristic fallback*.
- **Antislop Engineering UI**: Penerapan antarmuka dengan kepadatan informasi tinggi (*high-density data deck*), menghindari komponen dekoratif yang mengalihkan analisis data.

---

## 2. Landasan Teori & Tinjauan Pustaka

### 2.1 Microblogging dan Meta Threads
Meta Threads beroperasi menggunakan arsitektur Single Page Application (SPA) berbasis React yang memanfaatkan protokol GraphQL terenkripsi internal. Berbeda dengan halaman web tradisional berbasis server-rendered HTML, struktur DOM pada Threads dimuat secara asinkron (*lazy-loading*) dan komponen visual yang keluar dari batas layar (*viewport*) dilepaskan dari memori secara dinamis untuk efisiensi peramban.

### 2.2 Web Scraping Modern & Emulasi Headless (Playwright)
Otomatisasi pengumpulan data menggunakan pustaka Playwright bekerja langsung pada tingkat protokol DevTools (Chromium). Mekanisme ini memungkinkan:
- Intersepsi lalu lintas jaringan (*network interception*).
- Manipulasi konteks peramban untuk menyamarkan status otomatisasi (`navigator.webdriver = false`).
- Penjadwalan scroll bertahap (*progressive viewport scrolling*) yang meniru perilaku pembaca manusia guna menghindari *rate-limiting*.

### 2.3 Pemrosesan Bahasa Alami (NLP) Bahasa Indonesia & IndoBERT
Bahasa Indonesia memiliki keunikan morfologis aglutinatif dan variasi register bahasa informal yang tinggi di media sosial. Model **IndoBERT** (*Indonesian Bidirectional Encoder Representations from Transformers*) dilatih pada korpus Indo4B yang mencakup miliaran token teks bahasa Indonesia. Varian IndoNLU SMSA (*Sentiment Analysis*) yang digunakan dalam sistem ini mengadopsi mekanisme *self-attention* multi-kepala untuk menangkap ketergantungan semantik antarkata terlepas dari posisinya dalam kalimat.

### 2.4 Generative AI & Structured Output Parsing
Pada tingkat analisis semantik tingkat lanjut, Large Language Model (Gemini 2.5 Flash) dimanfaatkan melalui inferensi berbasis skema terstruktur (*Structured JSON Output*). Pendekatan ini memandu luaran probabilitas model agar mematuhi batasan skema Pydantic secara deterministik, menghasilkan label kategori, skor numerik, dan daftar entitas tanpa memerlukan tahapan *regex post-processing* yang rentan galat (*error-prone*).

---

## 3. Arsitektur dan Spesifikasi Sistem

Sistem mengadopsi arsitektur berlapis terpisah (*decoupled layered architecture*) yang terbagi atas tiga pilar utama: Lapisan Presentasi (Frontend), Lapisan Logika & Layanan (Backend & Worker), dan Lapisan Persistensi Data (Database).

```
                                      ┌────────────────────────────────────────┐
                                      │           Frontend (Client)            │
                                      │   SvelteKit 5 + TypeScript + Tailwind  │
                                      └──────────────────┬─────────────────────┘
                                                         │ HTTP / JSON REST
                                                         ▼
                                      ┌────────────────────────────────────────┐
                                      │            Backend (Server)            │
                                      │          FastAPI (Python 3.14)         │
                                      └───────┬────────────────────────┬───────┘
                                              │                        │
                     ┌────────────────────────┴────────┐      ┌────────┴────────────────────────┐
                     │ Background Scraping Worker      │      │ Inference & NLP Engine          │
                     │ - Playwright Stealth Scraper    │      │ - TextNormalizer Lexicon        │
                     │ - Official Threads API Client   │      │ - IndoBERT (IndoNLU SMSA)       │
                     │ - Snowflake Timestamp Decoder   │      │ - Gemini 2.5 Flash (google-genai│
                     └────────────────┬────────────────┘      └────────┬────────────────────────┘
                                      │                                │
                                      └────────────────┬───────────────┘
                                                       │ SQLAlchemy Async ORM
                                                       ▼
                                      ┌────────────────────────────────────────┐
                                      │         Database Persistensi           │
                                      │        PostgreSQL 16 (JSONB)           │
                                      └────────────────────────────────────────┘
```

### 3.1 Matriks Teknologi Komprehensif

| Kategori | Komponen | Versi | Peran Teknis dalam Sistem |
| :--- | :--- | :--- | :--- |
| **Backend Core** | FastAPI | 0.162.0 | Pengatur rute API asinkron, dokumentasi OpenAPI otomatis, dan validasi data. |
| **ASGI Engine** | Uvicorn | 0.54.0 | Server HTTP berbasis uvloop untuk menangani konkurensi I/O tinggi. |
| **Skema Data** | Pydantic | 2.14.3 | Validasi tipe data ketat pada request, response, dan output model AI. |
| **Scraping** | Playwright | 1.64.1 | Mesin otomasi Chromium nir-antarmuka (*headless*) berbasis event-loop. |
| **Model NLP Lokal** | Transformers & PyTorch | 5.22 / 2.15 | Inferensi lokal model IndoBERT berbasis CPU dengan multithreading teroptimasi. |
| **Model AI Awan** | Google GenAI SDK | 3.0.0 | Klien API Gemini Flash untuk analisis sentimen, emosi, dan ekstraksi entitas. |
| **ORM & Database** | SQLAlchemy & Asyncpg | 2.1.8 / 0.32 | Abstraksi relasional asinkron dan koneksi non-blocking ke PostgreSQL. |
| **Sistem Basis Data** | PostgreSQL | 16-Alpine | Penyimpanan terstruktur data postingan, relasi sentimen, dan log pekerjaan. |
| **Frontend Core** | SvelteKit | 3.0.0 (Svelte 5) | Antarmuka pengguna reaktif berbasis kompilator dan Svelte 5 Runes. |
| **Tipografi & Desain** | Tailwind CSS | 4.3.4 | Styling utilitas, pengelolaan variabel tema krisis (*Obsidian Palette*). |
| **Ikonografi** | Lucide Svelte | 1.0.1 | Indikator visual status sistem, navigasi, dan metrik. |
| **Kontainerisasi** | Docker Compose | v2 | Orkestrasi penyedia basis data PostgreSQL pada port host `5433`. |

---

## 4. Desain Skema Basis Data

Basis data dirancang dengan pemisahan tegas antara data mentah postingan (*raw post data*), hasil pengolahan kecerdasan buatan (*intelligence metadata*), serta rekam jejak pekerjaan (*audit logs*).

```
 ┌────────────────────────────────────────┐         ┌────────────────────────────────────────┐
 │                 posts                  │         │               sentiments               │
 ├────────────────────────────────────────┤         ├────────────────────────────────────────┤
 │ PK  id                 VARCHAR(128)    │◄──┐     │ PK  id                 UUID            │
 │     author_username    VARCHAR(128)    │   │     │ FK  post_id            VARCHAR(128)    │ (UNIQUE)
 │     author_name        VARCHAR(256)    │   └─────┤     sentiment_label    VARCHAR(32)     │
 │     author_profile_pic VARCHAR(1024)   │         │     confidence_score   FLOAT           │
 │     content            TEXT            │         │     primary_emotion    VARCHAR(64)     │
 │     post_url           VARCHAR(1024)   │         │     summary_reason     TEXT            │
 │     likes_count        INTEGER         │         │     locations          JSONB           │
 │     replies_count      INTEGER         │         │     entities           JSONB           │
 │     reposts_count      INTEGER         │         │     analyzed_at        TIMESTAMPTZ     │
 │     posted_at          TIMESTAMPTZ     │         └────────────────────────────────────────┘
 │     media_urls         JSONB           │
 │     raw_metadata       JSONB           │         ┌────────────────────────────────────────┐
 │     created_at         TIMESTAMPTZ     │         │              scraper_logs              │
 └────────────────────────────────────────┘         ├────────────────────────────────────────┤
                                                    │ PK  id                 UUID            │
                                                    │     keyword            VARCHAR(256)    │
                                                    │     method             VARCHAR(64)     │
                                                    │     status             VARCHAR(32)     │
                                                    │     posts_found        INTEGER         │
                                                    │     posts_inserted     INTEGER         │
                                                    │     error_message      TEXT            │
                                                    │     started_at         TIMESTAMPTZ     │
                                                    │     completed_at       TIMESTAMPTZ     │
                                                    │     created_at         TIMESTAMPTZ     │
                                                    └────────────────────────────────────────┘
```

### 4.1 Definisi Entitas Relasional
1. **Tabel `posts`**:
   - Berfungsi sebagai entitas utama penyimpan objek konten.
   - Kolom `id` bertindak sebagai Primary Key alami berbasis ID unik Threads (contoh: shortcode atau identifier numerik Meta).
   - Memiliki integritas referensial bertingkat (*ON DELETE CASCADE*) terhadap tabel sentimen.
2. **Tabel `sentiments`**:
   - Berisi hasil klasifikasi analitik. Kolom `post_id` bernilai unik (*1-to-1 relationship* terhadap `posts`).
   - Menyimpan atribut array `locations` dan `entities` dalam format biner `JSONB` yang mendukung pengindeksan GIN di masa depan.
3. **Tabel `scraper_logs`**:
   - Menyimpan riwayat eksekusi worker background untuk keperluan pemantauan status pekerjaan dan audit performa scraper.

---

## 5. Metodologi Komputasi & Implementasi Modul

### 5.1 Modul Akuisisi Data & Dekode Stempel Waktu (Scraper Pipeline)

Pengambilan data postingan dilakukan oleh kelas `PlaywrightThreadsScraper`. Untuk mengatasi keterbatasan antarmuka web publik Threads yang menampilkan waktu secara relatif (misal: *"3 jam lalu"*, *"1 hari lalu"*), sistem mengimplementasikan ekstraksi stempel waktu absolut berbasis dekode snowflake Instagram/Meta:

$$\text{Timestamp (ms)} = (\text{Snowflake ID} \gg 23) + 1314220021721$$

Di mana:
- $\text{Snowflake ID}$ dihitung dari representasi alfanumerik Base64 shortcode URL postingan Threads (`alphabet = [A-Za-z0-9-_]`).
- Nilai $1314220021721$ adalah konstanta *Instagram Epoch* (25 Agustus 2011 13:53:41.721 UTC).
- Operasi pergeseran bit kanan ($\gg 23$) memisahkan komponen stempel waktu dari nomor urut generator cluster internal Meta.

Implementasi ini menjamin postingan memiliki stempel waktu tanggal dan jam dengan ketepatan absolut berstandar UTC.

### 5.2 Modul Normalisasi & Pra-pemrosesan Teks (`TextNormalizer`)

Media sosial Indonesia didominasi ragam bahasa non-baku. Modul `TextNormalizer` menerapkan tahapan pembersihan terstruktur:
1. **Pembersihan Markup & Simbol Liar**: Menghapus tag HTML dan merapikan whitespace berlebih.
2. **Leksikon Slang & Singkatan Komprehensif**: Mengganti kata kunci non-baku menjadi leksikon formal:
   - Partikel kata hubung: `yg` $\rightarrow$ `yang`, `dgn` $\rightarrow$ `dengan`, `karna/krn` $\rightarrow$ `karena`, `tp/tpi` $\rightarrow$ `tapi`.
   - Negasi & modalitas: `gak/ga/nggak` $\rightarrow$ `tidak`, `gbs/gabisa` $\rightarrow$ `tidak bisa`.
   - Kata ganti: `gw/gua/gue` $\rightarrow$ `saya`, `lu/lo` $\rightarrow$ `kamu`.
   - Keluhan kesehatan kebencanaan: `sesek` $\rightarrow$ `sesak`, `napas/nafas` $\rightarrow$ `napas`, `gatel` $\rightarrow$ `gatal`, `ispa` $\rightarrow$ `infeksi saluran pernapasan`, `ispu` $\rightarrow$ `indeks pencemaran udara`.
   - Sensitivitas opini: `nirempati` $\rightarrow$ `tidak punya empati kejam jahat`.
3. **Preservasi Istilah Spesifik**: Istilah teknis lingkungan seperti *hotspot*, *hujan buatan*, *water bombing*, dan *BMKG* dipertahankan dalam bentuk aslinya.

### 5.3 Modul Klasifikasi Sentimen & Analisis Emosi Multi-Tier

Sistem menerapkan arsitektur toleransi kegagalan (*fault-tolerant multi-tier architecture*) dalam penentuan label sentimen:

```
                          ┌────────────────────────┐
                          │     Input Postingan    │
                          └───────────┬────────────┘
                                      │
                                      ▼
                        /────────────────────────────\
                       <  Pilih Engine (Konfigurasi)? >
                        \────────────────────────────/
                         /                          \
             (indobert) /                            \ (gemini / hybrid)
                       ▼                              ▼
          ┌────────────────────────┐     ┌────────────────────────┐
          │ IndoBERT Service       │     │ Gemini Flash Client    │
          │ (Hugging Face IndoNLU) │     │ (Structured Pydantic)  │
          └───────────┬────────────┘     └───────────┬────────────┘
                      │                              │
                      │ (Sukses)                     │ (Sukses)
                      ├──────────────────────────────┘
                      │
                      ▼ (Gagal / Terjadi Exception)
          ┌────────────────────────┐
          │ Fallback Engine        │
          │ Indonesian Heuristics  │
          └───────────┬────────────┘
                      │
                      ▼
          ┌────────────────────────┐
          │ Output Label Sentimen, │
          │ Skor Keyakinan & Emosi │
          └────────────────────────┘
```

#### A. IndoBERT Engine
- Menggunakan arsitektur model transformer klasifikasi urutan (`AutoModelForSequenceClassification`).
- Inferensi dijalankan dalam *batch* berukuran 16 postingan pada CPU dengan pembatasan multithreading (`torch.set_num_threads(4)`).
- Menghasilkan probabilitas *Softmax* untuk menentukan skor kepercayaan:

$$\text{Confidence} = \max_{k \in \{pos, neu, neg\}} \left( \frac{e^{z_k}}{\sum_{j} e^{z_j}} \right)$$

#### B. Gemini Flash Engine
- Menggunakan prompt terarah dengan keluaran skema Pydantic (`GeminiBatchSentimentOutput`).
- Membedah spektrum emosi warga ke dalam 5 taksonomi:
  - `anger`: Ditujukan kepada pelaku pembakaran lahan ilegal dan kelambanan regulasi.
  - `anxiety`: Kekhawatiran atas asap pekat dan ancaman penyakit paru-paru anak.
  - `sadness`: Kesedihan atas kerusakan ekosistem dan kondisi langit yang menguning/merah.
  - `hope`: Apresiasi atas turunnya hujan, keberhasilan pemadaman, dan operasi TMC (*Teknologi Modifikasi Cuaca*).
  - `neutral`: Laporan data numerik cuaca, arah angin BMKG, dan berita faktual.

### 5.4 Modul Formula Metrik: Net Sentiment Index (NSI)

Untuk merefleksikan tren polaritas masyarakat dalam satu nilai tunggal yang dapat dibandingkan lintas waktu, sistem menerapkan metrik **Net Sentiment Index (NSI)**:

$$\text{NSI} = \left( \frac{P - N}{P + U + N} \right) \times 100$$

Di mana:
- $P$ = Jumlah postingan dengan sentimen positif.
- $N$ = Jumlah postingan dengan sentimen negatif.
- $U$ = Jumlah postingan dengan sentimen netral.

Skala NSI bergerak dari $-100.0$ (seluruh sentimen negatif mutlak) hingga $+100.0$ (seluruh sentimen positif mutlak). Nilai mendekati $0$ mengindikasikan keseimbangan polaritas atau dominasi laporan faktual objektif.

---

## 6. Antarmuka Visualisasi & Desain Sistem

Antarmuka dibangun dengan panduan ketat **Antislop Design System**:
1. **Prinsip Estetika Data Kritis**:
   - Menghindari gradien neon dan ornamen dekoratif transparan berlebihan (*excessive glassmorphism*).
   - Menggunakan tema dasar *Deep Obsidian Slate* (`#090d16`) yang memberikan kontras tajam untuk pembacaan metrik jangka panjang tanpa menyebabkan kelelahan visual (*eye fatigue*).
   - Palet warna semantik:
     - Merah (*Crimson* `#ef4444`): Menandai sentimen negatif, kepulan asap parah, dan status bahaya ISPA.
     - Hijau (*Emerald* `#10b981`): Menandai sentimen positif, hujan deras, dan pemadaman berhasil.
     - Abu-abu/Slate (`#94a3b8`): Menandai data faktual dan laporan netral.
2. **Keterbacaan Numerik Tabular**:
   - Seluruh metrik statistik, persentase NSI, dan nilai waktu dirender menggunakan font monospace dengan pengaturan tabular (*proportional figures disabled*) agar angka tidak bergeser saat data diperbarui secara dinamis.
3. **Komponen Analitik**:
   - **Header & Scraper Modal**: Kontrol eksekusi scraping dengan pemilihan kueri, pembatasan kuota penarikan, dan monitor progres real-time.
   - **KPI Overview Cards**: Visualisasi total volume data, NSI, engagement pembaca (suka dan balasan), serta sebaran polaritas.
   - **Sentiment Timeline**: Grafik runtun waktu (*time series*) yang dapat diubah ke skala per jam (*hourly*) maupun per hari (*daily*).
   - **Regional Crisis Matrix**: Agregasi cerdas persebaran isu pada 5 provinsi episentrum Karhutla (Kalimantan Tengah, Riau, Kalimantan Barat, Jambi, dan Sumatera Selatan).
   - **Post Intelligence Feed**: Tampilan kartu percakapan warga dilengkapi filter sentimen, filter wilayah, pencarian kata kunci, serta tautan langsung ke tautan sumber Threads asli.

---

## 7. Rangkuman Spesifikasi API Backend

Backend menyediakan antarmuka RESTful API yang terdaftar di OpenAPI / Swagger documentation (`/api/v1/docs`):

| Method | Endpoint | Deskripsi Fungsi | Parameter Utama |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Pemeriksaan kesehatan layanan backend | - |
| `GET` | `/api/v1/analytics/overview` | Mengambil seluruh metrik KPI, distribusi emosi, dan ringkasan regional | - |
| `GET` | `/api/v1/analytics/timeline` | Mengambil data agregasi sentimen berbasis deret waktu | `days` (default: 3), `granularity` (`hour`/`day`) |
| `GET` | `/api/v1/posts/` | Mengambil daftar postingan dengan paginasi dan filter | `sentiment`, `keyword`, `location`, `page`, `limit` |
| `GET` | `/api/v1/posts/proxy-image` | Proxy streaming gambar Threads untuk menghindari blokir CORS/Referrer | `url` |
| `POST` | `/api/v1/scraper/trigger` | Memicu eksekusi scraping dan analitik di latar belakang | `keyword`, `method`, `max_posts`, `clear_existing` |
| `GET` | `/api/v1/scraper/status` | Mengambil riwayat dan status pekerjaan scraping terkini | `limit` (default: 5) |
| `POST` | `/api/v1/scraper/reset-stuck` | Mengatur ulang status pekerjaan yang mengalami kegagalan tak terduga | - |

---

## 8. Panduan Operasional Sistem

### 8.1 Menjalankan Basis Data
```bash
docker compose up -d postgres
```
Layanan PostgreSQL beroperasi pada port lokal `5433` (kredensial standar: `postgres:postgres`, basis data: `threads_karhutla`).

### 8.2 Menjalankan Backend Service
```bash
# Mengaktifkan environment virtual
source backend/venv/bin/activate

# Menjalankan server aplikasi
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Akses dokumentasi interaktif Swagger di: `http://localhost:8000/api/v1/docs`.

### 8.3 Menjalankan Frontend Dashboard
```bash
cd frontend
npm run dev
```
Akses antarmuka visualisasi pada peramban: `http://localhost:5173`.

---

## 9. Evaluasi Teknis & Kesimpulan

### 9.1 Evaluasi Teknis
1. **Keandalan Scraper**: Penerapan *Playwright Stealth* dengan penundaan humanistik berhasil mengumpulkan data percakapan publik secara stabil tanpa terblokir oleh mekanisme anti-bot Meta.
2. **Efisiensi Deduplikasi**: Pengecekan Primary Key sebelum inferensi AI berhasil memangkas redundansi komputasi hingga 100% pada postingan yang telah ada di basis data.
3. **Ketahanan Inferensi**: Model hibrida (IndoBERT + Gemini + Fallback Leksikon) menjamin sistem tidak pernah berhenti bekerja (*zero single-point-of-failure*) saat terjadi kendala jaringan atau pembatasan kuota kupon API.

### 9.2 Kesimpulan
Sistem *Karhutla Threads Scraping & Sentiment Intelligence* berhasil mendemonstrasikan integrasi komputasi yang menyeluruh: mulai dari pengumpulan data media sosial dinamis, standardisasi bahasa informal, inferensi kecerdasan buatan multi-tier, hingga penyajian intelijen krisis lingkungan secara ilmiah dan terukur. Proyek ini membuktikan kelayakan pemanfaatan platform Meta Threads sebagai instrumen observasi sosial kebencanaan di Indonesia.

---

## 10. Referensi & Daftar Pustaka

1. Koto, F., Rahimi, A., Lau, J. H., & Baldwin, T. (2020). *IndoLEM and IndoBERT: A Benchmark Dataset and Pre-trained Language Model for Indonesian NLP*. Proceedings of the 28th International Conference on Computational Linguistics (COLING 2020).
2. Purwarianti, A., & Lim, A. (2019). *IndoNLU: Benchmark and Resources for Evaluating Indonesian Natural Language Understanding*. arXiv preprint arXiv:2009.05387.
3. Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*. NAACL-HLT 2019.
4. Badan Restorasi Gambut dan Mangrove (BRGM) Republik Indonesia. (2023). *Panduan Pemantauan dan Pencegahan Kebakaran Lahan Gambut Terpadu*. Jakarta.
5. Badan Meteorologi, Klimatologi, dan Geofisika (BMKG). (2023). *Informasi Konsentrasi Partikulat (PM2.5) dan Sebaran Asap Akibat Karhutla*. Stasiun Klimatologi Nasional.
6. Meta Platforms, Inc. (2024). *Threads API Documentation: Threads Keyword Search and Media Endpoints*. Meta for Developers.

# ThreadScope - Universal Sentiment Intelligence

Sistem intelijen dan analisis sentimen multi-dimensi untuk memantau percakapan publik di platform **Threads (Meta)** secara dinamis untuk **topik apa pun** (hukum & peradilan, kebijakan publik, bencana alam, olahraga, teknologi, dll.).

---

## Fitur Utama

- **Pencarian Topik Universal & Dinamis**: Mendukung pencarian kueri apa pun secara dinamis dengan ekspansi subkueri dan adaptasi domain percakapan warganet Indonesia.
- **Deep IndoBERT & NLP Bahasa Gaul**:
  - Model *Fine-tuned* IndoBERT (`ayameRushia/bert-base-indonesian-1.5G-sentiment-analysis-smsa`).
  - Terjemahan semantik 50+ emoji media sosial agar tidak menjadi token `[UNK]`.
  - Kamus bahasa gaul, singkatan warganet, dan idiom majemuk (*"gacor parah"*, *"zonk parah"*, *"fix no debat"*).
  - Deteksi sarkasme multi-pola khusus gaya bahasa warganet Indonesia.
- **Deduplikasi 100% Anti-Duplikat**:
  - Hashing deterministik berbasis konten (SHA-256).
  - Filter deduplikasi berlapis (ID dan konten teks) sebelum masuk ke database.
- **Smart Link Routing**:
  - Membuka halaman asli postingan Threads (`https://www.threads.net/@user/post/code`) untuk data live.
  - Membuka feed pencarian langsung Threads bebas error 404.
  - Mendukung injeksi session cookie (`sessionid`) untuk melewati pembatasan tamu Meta (HTTP 429).
- **Dashboard Modern & Responsif**:
  - Dibangun dengan **SvelteKit 5 + Tailwind CSS v4**.
  - Visualisasi timeline sentimen, agregasi regional nasional, ekstraksi entitas, dan filter multi-dimensi.

---

## Tech Stack

- **Backend**: Python 3.11 - 3.14 + **FastAPI** + **SQLAlchemy (Async)** + **Uvicorn**
- **Machine Learning / NLP**: **PyTorch** + **Hugging Face Transformers (IndoBERT)**
- **Scraper Engine**: **Playwright Stealth Scraper**
- **Database**: **PostgreSQL** (didukung langsung atau via Docker)
- **Frontend**: **SvelteKit 5** + **Vite** + **Tailwind CSS v4** + **Lucide Icons**

---

## 🪟 Panduan Lengkap Instalasi & Menjalankan di Windows

Berikut panduan langkah demi langkah menjalankan ThreadScope di sistem operasi Windows (menggunakan **PowerShell** atau **Command Prompt**).

### 1. Prasyarat di Windows
Pastikan Anda telah menginstal perangkat lunak berikut:
1. **Git for Windows**: [Unduh Git](https://git-scm.com/download/win)
2. **Python 3.11 atau lebih baru**: [Unduh Python](https://www.python.org/downloads/windows/)
   *(PENTING: Saat instalasi Python di Windows, centang opsi **"Add python.exe to PATH"**)*.
3. **Node.js (LTS v20 atau v22)**: [Unduh Node.js](https://nodejs.org/)
4. **PostgreSQL**:
   - Opsi A (Installer Resmi): [Unduh PostgreSQL untuk Windows](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) (port default `5432`).
   - Opsi B (Docker Desktop): Jika menggunakan Docker Desktop for Windows.

---

### 2. Clone Repositori

Buka **PowerShell** atau **Terminal**, lalu clone repositori ini:

```powershell
git clone https://github.com/ferdiannada/thread-scope.git
cd thread-scope
```

---

### 3. Setup Database PostgreSQL di Windows

Buat database baru bernama `thread_scope` (atau `threads_karhutla`).

Jika menggunakan PostgreSQL lokal di Windows, buka terminal atau **SQL Shell (psql)**:
```sql
CREATE DATABASE thread_scope;
```
*(Catatan: Anda tidak perlu membuat tabel secara manual! FastAPI akan otomatis membuat semua tabel saat backend pertama kali dijalankan).*

---

### 4. Setup Backend (FastAPI + IndoBERT)

1. **Buat dan aktifkan Virtual Environment Python**:
   ```powershell
   cd backend
   python -m venv venv
   
   # Untuk PowerShell:
   .\venv\Scripts\Activate.ps1
   
   # Atau untuk Command Prompt (cmd):
   venv\Scripts\activate.bat
   ```

   *(Jika di PowerShell muncul error script execution policy, jalankan: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` lalu ulangi perintah aktivasi).*

2. **Instal Dependensi Backend**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   *(Tips untuk PyTorch di Windows: Jika ingin versi CPU yang lebih ringan, jalankan: `pip install torch --index-url https://download.pytorch.org/whl/cpu`)*.

3. **Instal Browser Playwright**:
   ```powershell
   playwright install chromium
   ```

4. **Konfigurasi Environment (`.env`)**:
   Salin file `.env.example` menjadi `.env` di folder root atau backend:
   ```powershell
   # Dari folder root project:
   copy .env.example .env
   ```
   Buka file `.env` dan sesuaikan koneksi database Anda, misalnya:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:password_anda@localhost:5432/thread_scope
   SENTIMENT_ENGINE=indobert
   PLAYWRIGHT_HEADLESS=true
   
   # Opsional: Jika ingin scraping live tanpa rate-limit Meta, masukkan cookie sessionid Brave/Chrome:
   THREADS_SESSION_ID=
   ```

5. **Jalankan Backend Server**:
   Dari folder utama project (`thread-scope`):
   ```powershell
   # Set PYTHONPATH dan jalankan uvicorn:
   $env:PYTHONPATH="backend"
   .\backend\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Swagger API Documentation dapat diakses di: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

### 5. Setup Frontend (SvelteKit Dashboard)

Buka jendela terminal / PowerShell **baru**, lalu jalankan:

```powershell
cd thread-scope\frontend
npm install
npm run dev
```

Buka peramban Anda di: **[http://localhost:5173](http://localhost:5173)**

---

## 🐧 Panduan untuk Linux / macOS

```bash
# 1. Clone & Setup Backend
git clone https://github.com/ferdiannada/thread-scope.git
cd thread-scope
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
playwright install chromium

# 2. Setup Environment
cp .env.example .env

# 3. Jalankan Backend
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Jalankan Frontend (Terminal Baru)
cd frontend
npm install
npm run dev
```

---

## 🧪 Menjalankan Pengujian (Unit Tests)

Untuk memvalidasi integrasi IndoBERT, kalibrasi sarkasme, dan keunikan postingan:

```bash
# Windows (PowerShell)
$env:PYTHONPATH="backend"
pytest backend\tests

# Linux / macOS
PYTHONPATH=backend pytest backend/tests
```

---

## Lisensi

Didistribusikan di bawah lisensi MIT. Silakan gunakan dan kembangkan untuk riset analisis sentimen media sosial di Indonesia.

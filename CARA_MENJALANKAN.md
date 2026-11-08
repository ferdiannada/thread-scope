# Panduan Menjalankan Sistem Karhutla Threads Scraping & Intelligence

Dokumen ini berisi panduan praktis dan lengkap untuk menjalankan seluruh komponen sistem: **Database PostgreSQL**, **Backend FastAPI**, dan **Frontend SvelteKit**.

---

## Prasyarat Sistem

Sebelum memulai, pastikan perangkat Anda telah terpasang:
- **Docker & Docker Compose** (untuk database PostgreSQL)
- **Python 3.11+ / 3.14** (beserta `venv` yang sudah disiapkan di `backend/venv`)
- **Node.js 20+** & **npm** (untuk dashboard frontend)

---

## 1. Menjalankan Database (PostgreSQL)

Database berjalan di dalam container Docker PostgreSQL 16 pada port host `5433` (agar tidak bentrok dengan instalasi PostgreSQL default port 5432).

1. Buka terminal pada root project:
   ```bash
   cd /home/nutrisari/Project/web/threads-scraping
   ```

2. Jalankan container di latar belakang (*detached mode*):
   ```bash
   docker compose up -d postgres
   ```

3. Periksa status container:
   ```bash
   docker ps --filter "name=karhutla_postgres"
   ```
   > **Informasi Database:**
   > - **Host:** `localhost`
   > - **Port:** `5433`
   > - **Database:** `threads_karhutla`
   > - **User / Password:** `postgres` / `postgres`

---

## 2. Menjalankan Backend (FastAPI)

Backend bertugas menangani REST API, scraping (Playwright / Official API), analisis sentimen (IndoBERT / Gemini), serta penyimpanan data.

1. Buka terminal baru dan masuk ke root project:
   ```bash
   cd /home/nutrisari/Project/web/threads-scraping
   ```

2. Aktifkan Python Virtual Environment:
   ```bash
   source backend/venv/bin/activate
   ```

3. *(Opsional)* Cek konfigurasi environment di file `backend/.env`:
   - Pastikan `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/threads_karhutla`
   - Pilihan sentiment engine: `SENTIMENT_ENGINE=indobert` (default lokal tanpa kuota) atau `gemini` (menggunakan `GEMINI_API_KEY`).

4. Jalankan server FastAPI dengan Uvicorn:
   ```bash
   PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. Akses Backend:
   - **Base URL:** [http://localhost:8000](http://localhost:8000)
   - **Swagger Interactive API Docs:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   - **ReDoc Documentation:** [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
   - **Health Check Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 3. Menjalankan Frontend (SvelteKit Dashboard)

Frontend dibangun dengan SvelteKit 5 + Tailwind CSS v4 dan telah dikonfigurasi reverse proxy ke backend port 8000.

1. Buka terminal baru dan arahkan ke direktori `frontend`:
   ```bash
   cd /home/nutrisari/Project/web/threads-scraping/frontend
   ```

2. Pastikan paket dependensi telah terinstal:
   ```bash
   npm install
   ```

3. Jalankan development server Vite:
   ```bash
   npm run dev
   ```

4. Akses Dashboard di peramban (browser):
   - **URL Dashboard:** [http://localhost:5173](http://localhost:5173)

---

## Ringkasan Port & Service

| Komponen | Service / Framework | Port / Akses | Keterangan |
|---|---|---|---|
| **Database** | PostgreSQL 16 Alpine | `localhost:5433` | Dikelola via `docker-compose.yml` |
| **Backend** | FastAPI + Uvicorn | `http://localhost:8000` | REST API, Docs di `/api/v1/docs` |
| **Frontend** | SvelteKit 5 + Vite | `http://localhost:5173` | Dashboard analitik & kontrol scraping |

---

## Perintah Cepat untuk Pengujian (Testing)

- **Unit & Integration Test Backend**:
  ```bash
  source backend/venv/bin/activate
  PYTHONPATH=backend pytest backend/tests
  ```

- **Pemeriksaan Type & Linter Frontend**:
  ```bash
  cd frontend
  npm run check
  ```

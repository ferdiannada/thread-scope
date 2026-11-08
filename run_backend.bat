@echo off
title ThreadScope - Backend Server
echo ===================================================
echo   ThreadScope - Backend Server (FastAPI + IndoBERT)
echo ===================================================
echo.

cd /d %~dp0backend

if not exist venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment belum ditemukan di folder backend\venv!
    echo Silakan jalankan setup terlebih dahulu:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Mengaktifkan Virtual Environment...
call venv\Scripts\activate.bat

echo Memeriksa file .env...
if not exist .env (
    if exist ..\.env (
        echo Menggunakan konfigurasi root .env...
    ) else (
        echo [PERINGATAN] File .env belum dibuat! Menyalin dari .env.example...
        copy .env.example .env
    )
)

echo Menjalankan Uvicorn Server di http://localhost:8000...
echo Tekan CTRL+C untuk menghentikan server.
echo.
uvicorn app.main:app --reload --port 8000
pause

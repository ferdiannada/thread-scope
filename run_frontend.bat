@echo off
title ThreadScope - Frontend Dashboard
echo ===================================================
echo   ThreadScope - Frontend Dashboard (SvelteKit)
echo ===================================================
echo.

cd /d %~dp0frontend

if not exist node_modules (
    echo [INFO] Folder node_modules belum ada. Menjalankan npm install...
    npm install
)

echo Menjalankan SvelteKit Dev Server di http://localhost:5173...
echo Tekan CTRL+C untuk menghentikan server.
echo.
npm run dev
pause

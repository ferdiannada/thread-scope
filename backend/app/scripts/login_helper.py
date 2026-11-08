import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

COOKIE_FILE = "threads_cookies.json"
ENV_FILE = ".env"


def update_env_session_id(session_id: str):
    """Updates or adds THREADS_SESSION_ID in .env file."""
    lines = []
    found = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        if line.strip().startswith("THREADS_SESSION_ID="):
            new_lines.append(f"THREADS_SESSION_ID={session_id}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"THREADS_SESSION_ID={session_id}\n")

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


async def auto_login():
    print("=" * 65)
    print(" 🚀 THREADS AUTO-LOGIN HELPER")
    print("=" * 65)
    print("Skrip ini akan membuka jendela peramban untuk Threads/Instagram.")
    print("Silakan login di jendela yang muncul.")
    print("Setelah login berhasil, sistem akan OTOMATIS menangkap sessionid")
    print("dan menyimpannya ke .env & threads_cookies.json tanpa perlu DevTools!\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="id-ID",
        )

        page = await context.new_page()
        print("Membuka https://www.threads.net/login...")
        try:
            await page.goto("https://www.threads.net/login", wait_until="domcontentloaded")
        except Exception as e:
            print(f"Peringatan navigasi: {e}")

        print("\n👉 Silakan lakukan login di jendela browser...")
        print("Menunggu deteksi sessionid (maksimal 3 menit)...")

        session_id = None
        all_cookies = []

        # Polling deteksi sessionid selama 180 detik
        for sec in range(120):
            await asyncio.sleep(1.5)
            try:
                cookies = await context.cookies()
                for c in cookies:
                    if c.get("name") == "sessionid" and c.get("value"):
                        session_id = c["value"]
                        all_cookies = cookies
                        break
                if session_id:
                    break
            except Exception:
                pass

        if session_id:
            print("\n✅ LOGIN BERHASIL TERDETEKSI SECARA OTOMATIS!")
            print(f"Session ID: {session_id[:8]}...{session_id[-6:]}")

            # 1. Simpan semua cookies ke threads_cookies.json
            with open(COOKIE_FILE, "w", encoding="utf-8") as f:
                json.dump(all_cookies, f, indent=2)
            print(f"💾 Disimpan ke: {COOKIE_FILE}")

            # 2. Update .env file
            update_env_session_id(session_id)
            print(f"💾 Disimpan ke: {ENV_FILE}")

            print("\n🎉 Selesai! Scraping Playwright sekarang otomatis menggunakan sesi ini")
            print("dan dapat mengambil 100% data live tanpa terhalang HTTP 429!")
        else:
            print("\n❌ Waktu tunggu habis atau login belum selesai. Silakan jalankan ulang skrip.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(auto_login())

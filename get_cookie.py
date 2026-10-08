import json
import asyncio
import os
import sys
from playwright.async_api import async_playwright
import pytz
from datetime import datetime
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

try:
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE_PATH)
except ImportError:
    if os.path.exists(ENV_FILE_PATH):
        try:
            with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

# Folder khusus tempat menyimpan sesi Playwright secara permanen
SESSION_DIR = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\PlaywrightSession"
OUTPUT_FILE = os.path.join(BASE_DIR, "token.json")

async def save_cookies_to_json_file(url: str, output_filepath: str):
    tz = pytz.timezone("Asia/Jakarta")
    captured_access_token = None

    async with async_playwright() as p:
        print("Launching Chrome browser...")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            channel="chrome",
            headless=False,
            args=["--profile-directory=Default"]
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Intercept Authorization Header dari traffic browser
        def handle_request(req):
            nonlocal captured_access_token
            auth_header = req.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                tok = auth_header.replace("Bearer ", "").strip()
                if tok and len(tok) > 50:
                    captured_access_token = tok

        # Intercept respons /auth/refresh jika dipanggil SPA
        async def handle_response(res):
            nonlocal captured_access_token
            if "/auth/refresh" in res.url:
                try:
                    res_json = await res.json()
                    tok = res_json.get("access_token")
                    if tok:
                        captured_access_token = tok
                except Exception:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)

        print("Opening MagangHub page...")
        try:
            await page.goto(url, wait_until="commit", timeout=45000)
        except Exception:
            pass

        await page.wait_for_timeout(3000)

        # Cek apakah terlempar ke halaman login
        if "login" in page.url.lower() or "auth" in page.url.lower():
            print("\nPlease log in via the opened browser.")
            print("   Waiting for you to complete login...\n")
            
            # Tunggu sampai URL berubah kembali ke halaman target/dashboard
            while "login" in page.url.lower() or "auth" in page.url.lower():
                await asyncio.sleep(2)
            
            print("Login detected! Capturing session data...")
            await page.wait_for_timeout(4000)
        else:
            print("Login session is still active.")

        # Tunggu beberapa detik agar seluruh API request frontend selesai
        await page.wait_for_timeout(3000)

        # Ambil seluruh cookies
        cookies = await context.cookies()

        # Cek localStorage jika access_token belum tertangkap dari network request
        if not captured_access_token:
            try:
                storage_token = await page.evaluate("""
                    () => {
                        for (let i = 0; i < localStorage.length; i++) {
                            const k = localStorage.key(i);
                            const v = localStorage.getItem(k);
                            if (v && v.startsWith('ey') && v.split('.').length === 3) return v;
                        }
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const k = sessionStorage.key(i);
                            const v = sessionStorage.getItem(k);
                            if (v && v.startsWith('ey') && v.split('.').length === 3) return v;
                        }
                        return null;
                    }
                """)
                if storage_token:
                    captured_access_token = storage_token
            except Exception:
                pass

        await context.close()

    # Ekstrak nilai monev_refresh_token dari cookies
    refresh_token_val = None
    for c in cookies:
        if c.get("name") == "monev_refresh_token":
            refresh_token_val = c.get("value")
            break

    # Jika access_token masih belum ada tetapi refresh token tersedia, panggil API refresh langsung
    if not captured_access_token and refresh_token_val:
        print("Refreshing access token via API...")
        try:
            cookie_dict = {c["name"]: c["value"] for c in cookies}
            api_base = os.getenv("MONEV_API_BASE", "https://monev-api.maganghub.kemnaker.go.id/api/v1")
            ref_headers = {
                "accept": "*/*",
                "origin": "https://monev.maganghub.kemnaker.go.id",
                "x-frontend-build-id": os.getenv("FRONTEND_BUILD_ID", "fdce5864ab936c3205233ffc340ba593c0136cd2-production"),
                "user-agent": os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
            }
            res = requests.post(
                f"{api_base}/auth/refresh",
                headers=ref_headers,
                cookies=cookie_dict,
                data=b"",
                timeout=15
            )
            if res.status_code in [200, 201]:
                captured_access_token = res.json().get("access_token")
                # Jika ada cookie baru dari respons refresh, perbarui
                if res.cookies.get("monev_refresh_token"):
                    refresh_token_val = res.cookies.get("monev_refresh_token")
        except Exception as e:
            print(f"Error refreshing via API: {e}")

    # Susun struktur token.json terpadu
    token_payload = {
        "access_token": captured_access_token or "",
        "monev_refresh_token": refresh_token_val or "",
        "cookies": cookies,
        "updated_at": datetime.now(tz).isoformat()
    }

    # Tulis/Simpan hasil ke file token.json
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(token_payload, f, indent=2, ensure_ascii=False)
        
    print("Success! Session saved to token.json.\n")
    return token_payload

def run_get_cookie_sync(output_filepath=OUTPUT_FILE):
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d")
    target_url = f"https://monev.maganghub.kemnaker.go.id/dashboard/riwayat?date={today_str}&view=edit"
    return asyncio.run(save_cookies_to_json_file(target_url, output_filepath))

if __name__ == "__main__":
    run_get_cookie_sync(OUTPUT_FILE)